"""
household.py — Value per *conversation*, not value per row.

Every locator in this business works from the same public list. The list is not
the edge. The edge is how much money one conversation is worth, and Wisconsin's
file quietly hands that to anyone who bothers to group it:

  • the same person is listed several times (different holders, different years),
    so five rows are really one human with five claims;
  • families share an address, and when one member is deceased the living ones
    at that address are the likely heirs — meaning the heir you have to "find"
    is often already sitting in your own data.

Grouping turns "5 letters to 5 strangers" into "1 phone call, 5 claims". That's
better economics for the operator AND less nagging for the household, which is
the only kind of edge worth building here.

PRIVACY RULE, enforced by design: a combined outreach document is only ever
assembled from ONE person's own claims (:func:`same_person_clusters`). Relatives
are surfaced to the OPERATOR as research leads (:func:`heir_bridges`) — we never
disclose one person's money to another person.

Pure computation over records already in hand. No network, no new data sources.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import compliance
import contact_finder

# Unit/secondary-address noise: everything from the marker on is dropped so
# "123 Main St Apt 4" and "123 Main St" land in the same household.
_UNIT_NOISE = re.compile(r"\b(?:APT|UNIT|STE|SUITE|FL|FLOOR|RM|ROOM|TRLR|LOT)\b.*$")
_PUNCT = re.compile(r"[.,'\"()#]")
# Wrappers that hide a person's real surname ("ESTATE OF DAVID KRAUSE" → KRAUSE).
_WRAPPERS = re.compile(
    r"\b(?:THE\s+)?(?:ESTATE|EST)\s+OF\b|\bESTATE\b|\bDECEASED\b|\bDECD\b"
    r"|\bTRUSTEE\b|\bTRUST\b|\bREVOCABLE\b|\bLIVING\b")
_ZIP = re.compile(r"\d{5}")
# Property types that mark a claim as belonging to someone who has died — the
# whole reason "heir finder" is the name of the trade.
_BENEFICIARY_TYPES = re.compile(r"BENEFICIAR|DEATH BENEFIT|SURVIVOR")

# One extra claim on the same person is worth a lot; the tenth is worth less.
LEVERAGE_PER_EXTRA_CLAIM = 0.12
LEVERAGE_CAP = 0.35


def _norm(s) -> str:
    return _PUNCT.sub("", str(s or "").upper()).replace("  ", " ").strip()


def _first_of(prospect: dict) -> str:
    """Canonical first name — nicknames fold into the formal name so 'Mike
    Hershberger' and 'Michael Hershberger' are recognized as one person."""
    raw = _norm(prospect.get("first") or "").split(" ")
    first = raw[0] if raw and raw[0] else contact_finder.parse_name(
        prospect.get("name", ""))["first"].upper()
    if not first:
        return ""
    # contact_finder's nickname map is two-way; the formal name is the member
    # that is NOT a known nickname of something else, so prefer the longest
    # alternative that maps back to this one. Deterministic either way.
    alts = contact_finder._NICK.get(first, set())
    formal = first
    for a in sorted(alts):
        if first in contact_finder._NICK.get(a, set()) and len(a) > len(formal):
            formal = a
    return formal


def _last_of(prospect: dict) -> str:
    """Surname with estate/trust wrappers stripped."""
    stripped = _WRAPPERS.sub(" ", _norm(prospect.get("name")))
    stripped = re.sub(r"\s+", " ", stripped).strip(" ,")
    last = _norm(prospect.get("last"))
    if last and last in stripped.split():
        return last
    toks = [t for t in stripped.split() if t not in contact_finder.SUFFIXES]
    return toks[-1] if toks else last


def address_key(prospect: dict) -> str:
    """A place two records can share. Street+zip when we have a street, else
    city — deliberately coarse-to-fine so a blank address still groups a family
    by city instead of pretending every record is unique."""
    raw = str(prospect.get("last_known_address") or "")
    street = _UNIT_NOISE.sub("", _norm(raw.split(",")[0])).strip()
    zip_m = _ZIP.search(str(prospect.get("zip") or "") or raw)
    zip_code = zip_m.group(0) if zip_m else ""
    city = _norm(prospect.get("city"))
    if len(street) > 4 and re.search(r"\d", street):
        return f"A:{street}|{zip_code or city}"
    if city:
        return f"C:{city}|{zip_code}"
    return ""


def person_key(prospect: dict) -> str:
    """Identity of one human: surname + canonical first name + place."""
    last, first = _last_of(prospect), _first_of(prospect)
    if not last or not first:
        return ""
    return f"{last}/{first}@{address_key(prospect) or '?'}"


def household_key(prospect: dict) -> str:
    """The unit a single conversation can cover: one surname at one place."""
    last, addr = _last_of(prospect), address_key(prospect)
    return f"{last}@{addr}" if last and addr else ""


def is_deceased(prospect: dict) -> bool:
    parsed = contact_finder.parse_name(prospect.get("name", ""))
    if parsed["deceased"]:
        return True
    return bool(_BENEFICIARY_TYPES.search(str(prospect.get("property_type") or "").upper()))


def _active(prospect: dict) -> bool:
    return str(prospect.get("suppression_status") or "ACTIVE").upper() != "SUPPRESSED"


@dataclass
class Leverage:
    """What one conversation with this person is actually worth."""
    claims: int = 1
    own_total: float = 0.0
    siblings: list = field(default_factory=list)   # other property_ids, same person
    household: str = ""
    household_size: int = 1
    household_total: float = 0.0

    @property
    def multiplier(self) -> float:
        """Priority boost for reaching someone who has more than one claim."""
        if self.claims <= 1:
            return 1.0
        return 1.0 + min(LEVERAGE_CAP, LEVERAGE_PER_EXTRA_CLAIM * (self.claims - 1))


@dataclass
class PersonCluster:
    key: str
    name: str
    members: list
    total: float
    address: str

    @property
    def fee_potential(self) -> float:
        return compliance.fee_amount(self.total)


@dataclass
class HeirBridge:
    """A deceased owner's claim whose likely heirs are already in our own list."""
    estate: dict
    candidates: list
    household: str

    @property
    def unlock(self) -> float:
        return compliance.fee_amount(self.estate.get("amount", 0))


@dataclass
class Household:
    key: str
    label: str
    address: str
    people: list          # list[list[dict]] — grouped by person
    claims: int
    total: float
    has_estate: bool
    reachable: bool

    @property
    def fee_potential(self) -> float:
        return compliance.fee_amount(self.total)


def _same_human(a: str, b: str) -> bool:
    """Are these two first names plausibly the same person, GIVEN that surname
    and address already match?

    The nickname table can never be complete — Wisconsin's file is full of
    "Bart/Bartholomew", "Kathy/Kathleen", and bare initials. Inside a single
    household the risk of a false merge is tiny and the cost of a missed merge is
    real (a duplicate letter to someone who already got one), so a prefix or an
    initial counts as a match. Different names of the same length never merge.
    """
    if a == b:
        return True
    if b in contact_finder._NICK.get(a, set()):
        return True
    if len(a) == 1 or len(b) == 1:              # "M Hershberger" ↔ "Michael"
        return a[0] == b[0]
    short, long_ = sorted((a, b), key=len)
    return len(short) >= 3 and long_.startswith(short)


def _merge_person_buckets(persons: dict[str, list]) -> dict[str, list]:
    """Fold buckets that are the same human under a different first name.

    Keys carry surname and address, so only buckets already sharing both are ever
    considered. The surviving key is the one with the longest (most formal) first
    name, which keeps the result stable no matter what order records arrive in.
    """
    by_place: dict[tuple, list] = {}
    for key in persons:
        name_part, _, place = key.partition("@")
        last, _, first = name_part.partition("/")
        by_place.setdefault((last, place), []).append((first, key))
    merged: dict[str, list] = {}
    for group in by_place.values():
        group.sort(key=lambda t: (-len(t[0]), t[0]))     # longest first name wins
        claimed: list[tuple[str, str]] = []
        for first, key in group:
            host = next((h for hf, h in claimed if _same_human(hf, first)), None)
            if host is None:
                claimed.append((first, key))
                merged.setdefault(key, []).extend(persons[key])
            else:
                merged[host].extend(persons[key])
    return merged


def build_graph(prospects: list[dict]) -> dict:
    """Index prospects into people and households. Businesses are excluded — a
    bank or a county is not a household and must never be grouped as family."""
    from scoring import segment  # local import: scoring imports nothing from here
    persons: dict[str, list] = {}
    houses: dict[str, list] = {}
    for p in prospects:
        if segment(p) == "BUSINESS":
            continue
        pk = person_key(p)
        if pk:
            persons.setdefault(pk, []).append(p)
        hk = household_key(p)
        if hk:
            houses.setdefault(hk, []).append(p)
    persons = _merge_person_buckets(persons)
    # A record's own key may have been merged away, so keep a direct lookup.
    owner = {}
    for key, members in persons.items():
        for m in members:
            owner[id(m)] = key
    return {"persons": persons, "houses": houses, "owner": owner}


def _bucket_for(prospect: dict, graph: dict) -> str:
    """Which merged person-bucket this record ended up in."""
    key = graph.get("owner", {}).get(id(prospect))
    if key:
        return key
    pid = prospect.get("property_id")
    for k, members in graph["persons"].items():
        if any(m.get("property_id") == pid for m in members):
            return k
    return person_key(prospect)


def leverage(prospect: dict, graph: dict) -> Leverage:
    pk, hk = _bucket_for(prospect, graph), household_key(prospect)
    mine = graph["persons"].get(pk) or [prospect]
    house = graph["houses"].get(hk) or [prospect]
    return Leverage(
        claims=len(mine),
        own_total=sum(float(m.get("amount") or 0) for m in mine),
        siblings=[m["property_id"] for m in mine
                  if m.get("property_id") != prospect.get("property_id")],
        household=hk,
        household_size=len(house),
        household_total=sum(float(m.get("amount") or 0) for m in house),
    )


def same_person_clusters(graph: dict) -> list[PersonCluster]:
    """People who appear more than once — one letter covers all their claims."""
    out = []
    for key, members in graph["persons"].items():
        active = [m for m in members if _active(m)]
        if len(active) < 2:
            continue
        active.sort(key=lambda m: -float(m.get("amount") or 0))
        addr = next((m.get("last_known_address") for m in active
                     if m.get("last_known_address")), active[0].get("city", "")) or ""
        out.append(PersonCluster(
            key=key, name=active[0].get("name", ""), members=active,
            total=sum(float(m.get("amount") or 0) for m in active), address=addr))
    return sorted(out, key=lambda c: -c.total)


def heir_bridges(graph: dict) -> list[HeirBridge]:
    """Deceased owner + living same-surname people at the same address.

    This is the heir-finding the trade is named after, except the research is
    already done: the relative is a record we hold, sometimes with a phone
    number we've already tracked down.
    """
    out = []
    for hk, members in graph["houses"].items():
        dead = [m for m in members if is_deceased(m) and _active(m)]
        living = [m for m in members if not is_deceased(m) and _active(m)]
        if not dead or not living:
            continue
        # Whoever we can already reach goes first.
        living = sorted(living, key=lambda m: (0 if (m.get("phone") or m.get("email")) else 1,
                                               -float(m.get("amount") or 0)))
        for d in dead:
            out.append(HeirBridge(estate=d, candidates=living, household=hk))
    return sorted(out, key=lambda b: -b.unlock)


def households(graph: dict) -> list[Household]:
    """Multi-record families, ranked by money reachable per conversation."""
    out = []
    for hk, members in graph["houses"].items():
        if len(members) < 2:
            continue
        active = [m for m in members if _active(m)]
        if not active:
            continue
        people: dict[str, list] = {}
        for m in active:
            people.setdefault(_bucket_for(m, graph), []).append(m)
        label = (active[0].get("last") or _last_of(active[0]) or "").title()
        addr = next((m.get("last_known_address") for m in active
                     if m.get("last_known_address")), active[0].get("city", "")) or "—"
        out.append(Household(
            key=hk, label=f"{label} household", address=addr,
            people=list(people.values()), claims=len(active),
            total=sum(float(m.get("amount") or 0) for m in active),
            has_estate=any(is_deceased(m) for m in active),
            reachable=any(m.get("phone") or m.get("email") for m in active)))
    return sorted(out, key=lambda h: -h.total)


def summary(prospects: list[dict]) -> dict:
    """Headline numbers for the operator brief / dashboard."""
    g = build_graph(prospects)
    clusters, bridges, hh = same_person_clusters(g), heir_bridges(g), households(g)
    return {
        "multi_claim_people": len(clusters),
        "claims_in_clusters": sum(len(c.members) for c in clusters),
        "cluster_value": sum(c.total for c in clusters),
        "conversations_saved": sum(len(c.members) - 1 for c in clusters),
        "heir_bridges": len(bridges),
        "heir_bridge_unlock": sum(b.unlock for b in bridges),
        "households": len(hh),
    }
