"""
contact_finder.py — Intelligent skip-tracing: find the *right* person.

The whole operation only helps someone if we reach the actual human the money
belongs to. A generic "search their name" link fails constantly — common names,
old addresses, people who moved or passed away. This module is the smarter
"find": it normalizes the name, generates the variants a real person actually
goes by, scores how findable they are, and builds a *ranked* plan of public
lookups tuned to that specific record — including the deceased→heir pivot that
is, literally, heir-finding.

Ethics & legality: this orchestrates PUBLIC records and standard people-search
sites — the same tools a licensed skip-tracer or journalist uses. No hacking, no
scraping behind logins, no purchased breach data. The goal is to reunite people
with their own money, so precision here is a kindness: the better the match, the
fewer wrong doors we knock on.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import quote_plus, quote

# ── Reference data (small, embedded — no network) ────────────────────────────
COMMON_SURNAMES = {
    "SMITH", "JOHNSON", "WILLIAMS", "BROWN", "JONES", "GARCIA", "MILLER", "DAVIS",
    "RODRIGUEZ", "MARTINEZ", "HERNANDEZ", "LOPEZ", "GONZALEZ", "WILSON", "ANDERSON",
    "THOMAS", "TAYLOR", "MOORE", "JACKSON", "MARTIN", "LEE", "PEREZ", "THOMPSON",
    "WHITE", "HARRIS", "SANCHEZ", "CLARK", "RAMIREZ", "LEWIS", "ROBINSON", "WALKER",
    "YOUNG", "ALLEN", "KING", "WRIGHT", "SCOTT", "HILL", "GREEN", "ADAMS", "NELSON",
    "BAKER", "HALL", "RIVERA", "CAMPBELL", "MITCHELL", "CARTER", "ROBERTS",
}
COMMON_FIRST = {
    "JAMES", "JOHN", "ROBERT", "MICHAEL", "WILLIAM", "DAVID", "RICHARD", "JOSEPH",
    "THOMAS", "CHARLES", "CHRISTOPHER", "DANIEL", "MATTHEW", "MARK", "DONALD",
    "MARY", "PATRICIA", "JENNIFER", "LINDA", "ELIZABETH", "BARBARA", "SUSAN",
    "JESSICA", "SARAH", "KAREN", "NANCY", "LISA", "MARGARET", "BETTY",
}
# Two-way nickname map for query variants.
_NICK_PAIRS = [
    ("ROBERT", "BOB"), ("ROBERT", "ROB"), ("WILLIAM", "BILL"), ("WILLIAM", "WILL"),
    ("JAMES", "JIM"), ("JAMES", "JIMMY"), ("MICHAEL", "MIKE"), ("RICHARD", "RICK"),
    ("RICHARD", "DICK"), ("JOSEPH", "JOE"), ("THOMAS", "TOM"), ("CHARLES", "CHUCK"),
    ("CHARLES", "CHARLIE"), ("DAVID", "DAVE"), ("STEVEN", "STEVE"), ("STEPHEN", "STEVE"),
    ("ANTHONY", "TONY"), ("DANIEL", "DAN"), ("MATTHEW", "MATT"), ("CHRISTOPHER", "CHRIS"),
    ("NICHOLAS", "NICK"), ("SAMUEL", "SAM"), ("BENJAMIN", "BEN"), ("EDWARD", "ED"),
    ("LAWRENCE", "LARRY"), ("GERALD", "JERRY"), ("MARGARET", "PEGGY"), ("MARGARET", "PEG"),
    ("ELIZABETH", "LIZ"), ("ELIZABETH", "BETH"), ("ELIZABETH", "BETTY"), ("KATHERINE", "KATE"),
    ("KATHERINE", "KATHY"), ("SUSAN", "SUE"), ("JENNIFER", "JEN"), ("PATRICIA", "PATTY"),
    ("DEBORAH", "DEBBIE"), ("REBECCA", "BECKY"), ("RONALD", "RON"), ("KENNETH", "KEN"),
]
_NICK = {}
for _full, _nick in _NICK_PAIRS:
    _NICK.setdefault(_full, set()).add(_nick)
    _NICK.setdefault(_nick, set()).add(_full)

SUFFIXES = {"JR", "SR", "II", "III", "IV", "V"}
# "ESTATE OF" must precede the bare "ESTATE" alternative so it's stripped whole.
DECEASED_HINTS = re.compile(r"\bTHE ESTATE OF\b|\bESTATE OF\b|\bEST OF\b|\bESTATE\b|\bDECEASED\b|\bDECD\b|\bLATE\b")
BUSINESS_HINTS = re.compile(r"\bLLC\b|\bINC\b|\bCORP\b|\bCOMPANY\b|\bCO\.?\b|\bLP\b|\bLTD\b|\bTRUST\b")
# A true business entity → find an officer/agent. A personal TRUST is deliberately
# excluded: there you find the trustee (a person), so it routes through the
# individual path, just flagged.
ENTITY_HINTS = re.compile(r"\bLLC\b|\bINC\b|\bCORP\b|\bCOMPANY\b|\bCO\.?\b|\bLP\b|\bLTD\b|DISSOLVED")
US_STATES = {"AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
             "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
             "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
             "VA","WA","WV","WI","WY","DC"}


@dataclass
class Strategy:
    label: str
    kind: str          # people-search | public-record | obituary | genealogy | social | search
    url: str
    why: str
    precision: str     # high | medium | low

    def as_dict(self):
        return self.__dict__.copy()


@dataclass
class ContactPlan:
    property_id: str
    display_name: str
    parsed: dict
    location: dict
    findability: float
    findability_label: str
    deceased_likely: bool
    is_entity: bool
    strategies: list
    tips: list = field(default_factory=list)

    def as_dict(self):
        d = self.__dict__.copy()
        d["strategies"] = [s.as_dict() for s in self.strategies]
        return d


# ── Parsing ──────────────────────────────────────────────────────────────────
def parse_name(raw: str) -> dict:
    """Return {first, middle, last, suffix, clean, variants[]}. Handles 'LAST, FIRST'."""
    s = re.sub(r"\s+", " ", (raw or "").strip())
    deceased = bool(DECEASED_HINTS.search(s.upper()))
    # strip estate/deceased/trust wrappers to get to the person's name
    core = re.sub(DECEASED_HINTS, "", s.upper())
    core = re.sub(r"\bTRUST(EE)?\b|\bLIVING TRUST\b|\bREVOCABLE\b|\bOF\b", " ", core)
    core = re.sub(r"\s+", " ", core).strip(" ,")
    first = middle = last = suffix = ""
    comma = "," in core
    if comma:                              # "LAST, FIRST MIDDLE"
        last_part, _, rest = core.partition(",")
        last = last_part.strip()
        toks = rest.split()
    else:                                  # "FIRST MIDDLE LAST [SUFFIX]"
        toks = core.split()
    # strip any suffix token FIRST, before choosing the last name
    kept = []
    for t in toks:
        if t in SUFFIXES:
            suffix = t
        else:
            kept.append(t)
    toks = kept
    if not comma and len(toks) >= 2:       # last name is the final remaining token
        last = toks[-1]; toks = toks[:-1]
    if toks:
        first = toks[0]
        middle = " ".join(toks[1:]) if len(toks) > 1 else ""
    clean = " ".join(x for x in [first, middle, last] if x).title()
    return {"first": first.title(), "middle": middle.title(), "last": last.title(),
            "suffix": suffix.title(), "clean": clean, "deceased": deceased,
            "variants": _name_variants(first, middle, last)}


def _name_variants(first: str, middle: str, last: str) -> list:
    """The names a real person is actually listed under."""
    out = []
    def add(fn):
        v = " ".join(x for x in [fn, last] if x).title()
        if v and v not in out:
            out.append(v)
    add(first)
    if middle:
        add(f"{first} {middle[0]}")        # First M. Last
    for nick in sorted(_NICK.get(first, set())):
        add(nick)
    return out


def parse_location(address: str) -> dict:
    """Split a last-known address into street / city / state / zip (best effort)."""
    addr = (address or "").strip()
    up = addr.upper()
    parts = [p.strip() for p in addr.split(",") if p.strip()]
    street = parts[0] if parts else ""
    # ZIP: the last 5-digit group anywhere in the string.
    zips = re.findall(r"\b(\d{5})(?:-\d{4})?\b", addr)
    zc = zips[-1] if zips else ""
    # STATE: a real 2-letter state code, preferably the one just before the ZIP.
    state = ""
    m = re.search(r"\b([A-Z]{2})\b(?=[\s,]*\d{5})", up)
    if m and m.group(1) in US_STATES:
        state = m.group(1)
    if not state:
        for tok in re.findall(r"\b([A-Z]{2})\b", up):
            if tok in US_STATES:
                state = tok; break
    # CITY: the comma-part before the state/zip tail (usually parts[1]),
    # with any trailing "ST ZIP" stripped off.
    city = ""
    if len(parts) >= 2:
        cand = parts[1]
        cand = re.sub(r"\b[A-Z]{2}\b\s*\d{5}(?:-\d{4})?\s*$", "", cand, flags=re.I).strip()
        cand = re.sub(r"\b\d{5}(?:-\d{4})?\s*$", "", cand).strip()
        # if parts[1] was actually "ST ZIP", the city is unknown here
        city = cand if not re.fullmatch(r"[A-Z]{2}", cand.upper()) else ""
    return {"street": street, "city": city.title() if city else "",
            "state": state or "WI", "zip": zc}


# ── Findability ──────────────────────────────────────────────────────────────
def findability(parsed: dict, loc: dict) -> tuple[float, str]:
    """0–100 estimate of how reachable this person is, with a plain label."""
    if not parsed.get("last"):
        return 12.0, "Very hard"
    score = 58.0
    fu, lu = parsed["first"].upper(), parsed["last"].upper()
    if parsed.get("middle"):
        score += 14                        # a middle name disambiguates hugely
    if lu in COMMON_SURNAMES:
        score -= 16
    else:
        score += 8
    if fu in COMMON_FIRST and lu in COMMON_SURNAMES:
        score -= 12                        # "John Smith" problem
    if parsed.get("suffix"):
        score += 6
    if loc.get("city"):
        score += 12
    if loc.get("zip"):
        score += 9
    if parsed.get("deceased"):
        score -= 14                        # must find the heir, not the owner
    score = max(5.0, min(97.0, score))
    label = ("Easy" if score >= 75 else "Moderate" if score >= 50
             else "Hard" if score >= 30 else "Very hard")
    return round(score, 1), label


# ── Plan building ────────────────────────────────────────────────────────────
def _people_search_urls(name: str, city: str, state: str) -> list:
    n_plus = quote_plus(name)
    n_dash = quote(name.replace(" ", "-"))
    csz = quote_plus(f"{city}, {state}".strip(", ")) if city else quote_plus(state)
    city_dash = quote((city or "").replace(" ", "-"))
    return [
        Strategy("TruePeopleSearch", "people-search",
                 f"https://www.truepeoplesearch.com/results?name={n_plus}&citystatezip={csz}",
                 "Free current phone + address + relatives. Best first stop.", "high"),
        Strategy("FastPeopleSearch", "people-search",
                 f"https://www.fastpeoplesearch.com/name/{n_dash}_{city_dash}-{state.lower()}"
                 if city else f"https://www.fastpeoplesearch.com/name/{n_dash}_{state.lower()}",
                 "Free, strong on relatives and address history.", "high"),
        Strategy("ThatsThem", "people-search",
                 f"https://thatsthem.com/name/{n_dash}/{city_dash}-{state}" if city
                 else f"https://thatsthem.com/name/{n_dash}", "Free, adds email + phone.", "medium"),
        Strategy("WhitePages", "people-search",
                 f"https://www.whitepages.com/name/{n_dash}/{city_dash}-{state}" if city
                 else f"https://www.whitepages.com/name/{n_dash}/{state}",
                 "Good for confirming a match; some data gated.", "medium"),
    ]


def build_plan(prospect: dict) -> ContactPlan:
    name = prospect.get("name", "")
    parsed = parse_name(name)
    loc = parse_location(prospect.get("last_known_address", ""))
    is_entity = bool(ENTITY_HINTS.search(name.upper()))
    fscore, flabel = findability(parsed, loc)
    strategies: list[Strategy] = []
    tips: list[str] = []

    primary = parsed["variants"][0] if parsed["variants"] else parsed["clean"] or name
    city, state = loc["city"], loc["state"]

    if is_entity:
        # Dissolved business / trust → chase the registered agent / officers.
        q = quote_plus(f"{name} Wisconsin registered agent OR officer")
        strategies.append(Strategy("WI business entity search", "public-record",
            "https://apps.dfi.wi.gov/apps/corpsearch/Advanced.aspx",
            "Find the entity's registered agent and principals to contact.", "high"))
        strategies.append(Strategy("Google — officers/agent", "search",
            f"https://www.google.com/search?q={q}", "Surface the people behind the entity.", "medium"))
        tips.append("This is an entity, not a person — locate an authorized officer or the "
                    "registered agent, and expect corporate-authority documents.")
    else:
        # A real individual → people-search first, then confirm.
        strategies += _people_search_urls(primary, city, state)
        # High-precision search-engine query with location + intent
        gq = quote_plus(f'"{primary}" {city} {state} phone'.strip())
        strategies.append(Strategy("Google — name + city + phone", "search",
            f"https://www.google.com/search?q={gq}",
            "Catches listings the aggregators miss.", "medium"))
        # Property/tax records often carry a current mailing address
        pq = quote_plus(f"{primary} property tax records {city} Wisconsin".strip())
        strategies.append(Strategy("Property / tax records", "public-record",
            f"https://www.google.com/search?q={pq}",
            "County property records list a current owner mailing address.", "medium"))
        # Social as a soft confirm
        fq = quote_plus(primary)
        strategies.append(Strategy("Facebook people search", "social",
            f"https://www.facebook.com/search/people/?q={fq}",
            "Confirm the person still lives in the area; message respectfully.", "low"))

    if parsed.get("deceased"):
        # The heir-finding pivot: the owner passed → find surviving family (the claimants).
        oq = quote_plus(f"{parsed['clean']} obituary {city} Wisconsin".strip())
        strategies.insert(0, Strategy("Obituary search (Legacy)", "obituary",
            f"https://www.legacy.com/search?query={quote_plus(parsed['clean'])}",
            "Obituaries name surviving spouse and children — your actual claimants.", "high"))
        strategies.append(Strategy("Google — obituary + survivors", "obituary",
            f"https://www.google.com/search?q={oq}", "Reconstruct the family tree from the obit.", "high"))
        strategies.append(Strategy("FamilySearch (free genealogy)", "genealogy",
            f"https://www.familysearch.org/search/record/results?q.surname={quote(parsed['last'])}"
            f"&q.givenName={quote(parsed['first'])}", "Free records to verify heirs.", "medium"))
        tips.append("Owner is likely deceased — this is an ESTATE case. Find the surviving "
                    "heir(s) via the obituary, then treat it as the premium/contract track "
                    "with proper documentation.")

    if fscore < 40:
        tips.append("Low findability (common name / thin address). Lean on the middle name, "
                    "relatives listed on people-search sites, and the property records to "
                    "disambiguate before reaching out.")
    if parsed.get("variants") and len(parsed["variants"]) > 1:
        tips.append("Try these name variants too: " + ", ".join(parsed["variants"][1:]) + ".")

    return ContactPlan(
        property_id=prospect.get("property_id", ""), display_name=parsed["clean"] or name,
        parsed=parsed, location=loc, findability=fscore, findability_label=flabel,
        deceased_likely=parsed.get("deceased", False), is_entity=is_entity,
        strategies=strategies, tips=tips)


if __name__ == "__main__":
    for demo in [
        {"property_id": "1", "name": "Robert Anderson", "last_known_address": "12 Oak St, Madison, WI 53703"},
        {"property_id": "2", "name": "ESTATE OF MARGARET P KOWALSKI", "last_known_address": "44 Birch Ave, Eau Claire, WI 54701"},
        {"property_id": "3", "name": "Zephyrina Qubillfeather", "last_known_address": "9 Lake Rd, Bayfield, WI 54814"},
    ]:
        p = build_plan(demo)
        print(f"\n{p.display_name}  ·  findability {p.findability} ({p.findability_label})"
              f"{'  · DECEASED→heir' if p.deceased_likely else ''}")
        for s in p.strategies[:4]:
            print(f"  [{s.precision:6}] {s.label}")
