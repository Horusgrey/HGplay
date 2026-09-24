"""Lock the skip-trace engine — name/location parsing, findability, and the plan."""
import contact_finder as cf


def test_parse_name_first_last_with_suffix():
    p = cf.parse_name("Robert Anderson Jr")
    assert (p["first"], p["last"], p["suffix"]) == ("Robert", "Anderson", "Jr")


def test_parse_name_last_comma_first():
    p = cf.parse_name("KOWALSKI, JOHN A")
    assert p["first"] == "John" and p["last"] == "Kowalski" and p["middle"] == "A"


def test_parse_name_strips_estate_wrapper_and_flags_deceased():
    p = cf.parse_name("ESTATE OF MARGARET P KOWALSKI")
    assert p["deceased"] is True
    assert p["first"] == "Margaret" and p["last"] == "Kowalski"
    assert "Of" not in p["clean"]              # the wrapper is gone, not left behind


def test_name_variants_include_nicknames():
    v = cf.parse_name("Robert Anderson")["variants"]
    assert "Bob Anderson" in v and "Robert Anderson" in v


def test_parse_location_does_not_mistake_street_for_state():
    loc = cf.parse_location("12 Oak St, Madison, WI 53703")
    assert loc["state"] == "WI" and loc["zip"] == "53703" and loc["city"] == "Madison"


def test_findability_common_name_lower_than_rare():
    common = cf.findability(cf.parse_name("John Smith"), {"state": "WI"})[0]
    rare = cf.findability(cf.parse_name("Zephyrina Qubillfeather"),
                          {"city": "Madison", "state": "WI", "zip": "53703"})[0]
    assert rare > common


def test_deceased_plan_leads_with_obituary():
    plan = cf.build_plan({"property_id": "1", "name": "ESTATE OF A B",
                          "last_known_address": "1 St, Madison, WI 53703"})
    assert plan.deceased_likely
    assert plan.strategies[0].kind == "obituary"   # heir-finding pivot first


def test_entity_plan_targets_the_business_registry():
    plan = cf.build_plan({"property_id": "2", "name": "ACME HOLDINGS LLC",
                          "last_known_address": "1 St, Madison, WI"})
    assert plan.is_entity
    assert any(s.kind == "public-record" for s in plan.strategies)


def test_individual_plan_leads_with_people_search():
    plan = cf.build_plan({"property_id": "3", "name": "Jane Doe",
                          "last_known_address": "1 St, Madison, WI 53703"})
    assert plan.strategies[0].kind == "people-search"
    assert plan.findability > 0
