"""Lock the auto-fill: mock by default, writes contact onto the prospect, respects suppression."""
import skiptrace


def test_mock_provider_is_default_without_key(monkeypatch):
    monkeypatch.delenv("SKIPTRACE_API_KEY", raising=False)
    assert skiptrace.get_provider().name == "mock"


def test_mock_result_is_flagged_demo():
    r = skiptrace.trace({"name": "Gokhan Kiyak",
                         "last_known_address": "1 A St, Franklin, WI 53132"},
                        provider=skiptrace.MockProvider())
    assert r.demo is True and r.phone and "@" in r.email


def test_mock_is_deterministic():
    p = {"name": "Jane Doe", "last_known_address": "1 A St, Madison, WI"}
    a = skiptrace.trace(p, provider=skiptrace.MockProvider())
    b = skiptrace.trace(p, provider=skiptrace.MockProvider())
    assert a.phone == b.phone


def test_enrich_writes_contact_and_advances(crm):
    crm.add_prospect({"property_id": "K1", "name": "Gokhan Kiyak",
                      "last_known_address": "8459 S River Terrace Dr, Franklin, WI 53132"})
    res = skiptrace.enrich(crm, "K1", provider=skiptrace.MockProvider())
    assert res["success"] and "phone" in res["filled"]
    p = crm.get_prospect("K1")
    assert p["phone"] and p["stage"] == "ENRICHED"


def test_enrich_does_not_overwrite_existing_contact(crm):
    crm.add_prospect({"property_id": "K2", "name": "Has Phone", "phone": "(414) 555-0001",
                      "last_known_address": "1 A St, Milwaukee, WI"})
    skiptrace.enrich(crm, "K2", provider=skiptrace.MockProvider())
    assert crm.get_prospect("K2")["phone"] == "(414) 555-0001"   # kept, not clobbered


def test_enrich_refuses_suppressed(crm):
    crm.add_prospect({"property_id": "K3", "name": "Opted Out"})
    crm.suppress("K3")
    assert skiptrace.enrich(crm, "K3", provider=skiptrace.MockProvider())["error"] == "suppressed"
