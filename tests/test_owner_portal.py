"""Lock the owner-facing consent + opt-out behavior."""


def test_record_consent_sets_consent_and_advances(crm):
    crm.add_prospect({"property_id": "O1", "name": "Owner One", "stage": "CONTACTED"})
    assert crm.record_consent("O1") is True
    p = crm.get_prospect("O1")
    assert p["consent_status"] == "GIVEN"
    assert p["stage"] == "RESPONDED"


def test_record_consent_refused_for_suppressed(crm):
    crm.add_prospect({"property_id": "O2", "name": "Owner Two"})
    crm.suppress("O2", "opt out")
    assert crm.record_consent("O2") is False
    assert crm.get_prospect("O2")["stage"] == "SUPPRESSED"   # opt-out never overridden


def test_record_consent_does_not_downgrade_advanced_stage(crm):
    crm.add_prospect({"property_id": "O3", "name": "Owner Three", "stage": "SIGNED"})
    crm.record_consent("O3")
    # Already past RESPONDED — consent recorded but stage not pulled backwards.
    assert crm.get_prospect("O3")["stage"] == "SIGNED"
    assert crm.get_prospect("O3")["consent_status"] == "GIVEN"
