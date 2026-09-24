"""
skiptrace.py — Auto-fill a prospect's phone/email from a data provider.

This is the "the number appears by itself" feature. The honest mechanics:

  • Free people-search SITES block automated copying, so the app can't scrape
    them. To auto-populate a real phone/email it must call a paid data API — a
    few cents per lookup. That provider is swappable; you bring the API key.
  • With no key configured, this runs a MockProvider that returns clearly-fake,
    deterministic data (flagged demo=True) so the whole flow is visible and
    testable without spending a cent — and without pretending it's real.

Enrichment writes the found phone/email straight onto the prospect, so the rest
of the system (outreach, letters, the operator brief) picks it up automatically.
Ethics unchanged: public contact data to reunite people with their own money.
"""
from __future__ import annotations

import os
import hashlib
import json
from dataclasses import dataclass, asdict
from urllib import request as _req, error as _err

import contact_finder


@dataclass
class TraceResult:
    phone: str = ""
    email: str = ""
    address: str = ""
    confidence: float = 0.0        # 0..1
    source: str = ""
    demo: bool = False             # True when it's mock data, not a real lookup
    note: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


class SkipTraceProvider:
    """Interface. Implement lookup() for a real data vendor."""
    name = "base"

    def lookup(self, parsed: dict, location: dict) -> TraceResult:
        raise NotImplementedError


class MockProvider(SkipTraceProvider):
    """Deterministic fake data — for demos and tests. NEVER real contact info."""
    name = "mock"

    def lookup(self, parsed: dict, location: dict) -> TraceResult:
        seed = f"{parsed.get('first','')}{parsed.get('last','')}{location.get('city','')}"
        h = hashlib.sha1(seed.encode()).hexdigest()
        area = ["414", "608", "715", "920", "262"][int(h[:2], 16) % 5]
        num = f"({area}) 555-{int(h[2:6],16) % 10000:04d}"
        email = f"{parsed.get('first','x').lower()}.{parsed.get('last','y').lower()}@example.com"
        return TraceResult(phone=num, email=email, address=location.get("street", ""),
                           confidence=0.5, source="mock", demo=True,
                           note="Demo data — configure SKIPTRACE_API_KEY for real lookups.")


class GenericHTTPProvider(SkipTraceProvider):
    """A configurable adapter for a real people-data API.

    Configure via environment (so no secrets live in code):
      SKIPTRACE_API_URL   — the endpoint that accepts a JSON body and returns JSON
      SKIPTRACE_API_KEY   — sent as the `Authorization: Bearer <key>` header
      SKIPTRACE_PHONE_PATH, SKIPTRACE_EMAIL_PATH — dotted paths into the response
                            JSON (e.g. "person.phones.0.number"); defaults try
                            common shapes.

    This posts {first,last,city,state,zip,street} and reads the result. Different
    vendors differ slightly; the path env vars let you map yours without code.
    """
    name = "http"

    def __init__(self):
        self.url = os.environ.get("SKIPTRACE_API_URL", "")
        self.key = os.environ.get("SKIPTRACE_API_KEY", "")
        self.phone_path = os.environ.get("SKIPTRACE_PHONE_PATH", "")
        self.email_path = os.environ.get("SKIPTRACE_EMAIL_PATH", "")

    @staticmethod
    def _dig(obj, path):
        cur = obj
        for part in [p for p in path.split(".") if p]:
            try:
                cur = cur[int(part)] if part.isdigit() else cur.get(part)
            except (KeyError, IndexError, TypeError, AttributeError):
                return ""
            if cur is None:
                return ""
        return cur if isinstance(cur, str) else ""

    def _first_phone(self, data):
        if self.phone_path:
            return self._dig(data, self.phone_path)
        for p in ("phone", "phone_number", "phoneNumber"):
            if isinstance(data.get(p), str):
                return data[p]
        return ""

    def _first_email(self, data):
        if self.email_path:
            return self._dig(data, self.email_path)
        for e in ("email", "email_address", "emailAddress"):
            if isinstance(data.get(e), str):
                return data[e]
        return ""

    def lookup(self, parsed: dict, location: dict) -> TraceResult:
        if not (self.url and self.key):
            return MockProvider().lookup(parsed, location)
        payload = json.dumps({
            "first_name": parsed.get("first", ""), "last_name": parsed.get("last", ""),
            "city": location.get("city", ""), "state": location.get("state", "WI"),
            "zip": location.get("zip", ""), "street": location.get("street", ""),
        }).encode()
        req = _req.Request(self.url, data=payload, method="POST", headers={
            "Content-Type": "application/json", "Authorization": f"Bearer {self.key}"})
        try:
            with _req.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
        except (_err.URLError, ValueError, TimeoutError) as e:
            return TraceResult(source=self.name, note=f"Lookup failed: {e}")
        return TraceResult(phone=self._first_phone(data), email=self._first_email(data),
                           confidence=0.8, source=self.name, demo=False,
                           note="Live lookup.")


def get_provider() -> SkipTraceProvider:
    """Real provider when a key is configured; otherwise the safe mock."""
    return GenericHTTPProvider() if os.environ.get("SKIPTRACE_API_KEY") else MockProvider()


def trace(prospect: dict, provider: SkipTraceProvider | None = None) -> TraceResult:
    provider = provider or get_provider()
    plan = contact_finder.build_plan(prospect)
    return provider.lookup(plan.parsed, plan.location)


def enrich(crm, property_id: str, provider: SkipTraceProvider | None = None) -> dict:
    """Look up contact info and write it onto the prospect. Skips suppressed records."""
    p = crm.get_prospect(property_id)
    if not p:
        return {"error": "not found"}
    if p.get("suppression_status") == "SUPPRESSED":
        return {"error": "suppressed"}
    res = trace(p, provider)
    fields = {}
    if res.phone and not p.get("phone"):
        fields["phone"] = res.phone
    if res.email and not p.get("email"):
        fields["email"] = res.email
    if fields:
        crm.update_prospect(property_id, **fields)
        if p["stage"] == "IDENTIFIED":
            crm.update_stage(property_id, "ENRICHED", f"Auto contact ({res.source})")
        crm.log_contact_attempt(property_id, "SkipTrace",
                                "Demo Enrichment" if res.demo else "Enriched",
                                f"{res.source}: {res.phone} {res.email}".strip())
    return {"success": True, **res.as_dict(), "filled": list(fields.keys())}


if __name__ == "__main__":
    demo = {"property_id": "1", "name": "Gokhan Kiyak",
            "last_known_address": "8459 S River Terrace Dr, Franklin, WI 53132"}
    print("provider:", get_provider().name)
    print(json.dumps(trace(demo).as_dict(), indent=2))
