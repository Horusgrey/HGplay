"""Lock the prioritization logic — the 'high dollar ≠ high priority' principle."""
import scoring


def test_segment_classification():
    assert scoring.segment({"name": "ESTATE OF J. SMITH"}) == "ESTATE"
    assert scoring.segment({"name": "The Doe Family Trust"}) == "TRUST"
    assert scoring.segment({"name": "Acme LLC"}) == "BUSINESS"
    assert scoring.segment({"name": "Jane Q. Public"}) == "OWNER"


def test_holder_does_not_contaminate_segment():
    # An individual whose funds came from a corporation is still an OWNER,
    # not a BUSINESS — the holder must never drive the claimant segment.
    assert scoring.segment({"name": "Ada Fauxname", "holder": "COINBASE INC"}) == "OWNER"
    assert scoring.segment({"name": "Bob Real", "holder": "METLIFE INSURANCE CO"}) == "OWNER"


def test_suppressed_scores_zero():
    l = scoring.score_prospect({"property_id": "1", "name": "X", "amount": 100000,
                                "suppression_status": "SUPPRESSED", "eligibility_reviewed": True})
    assert l.score == 0.0 and l.track == "SUPPRESSED"


def test_unverified_routes_to_verify_first():
    l = scoring.score_prospect({"property_id": "1", "name": "X", "amount": 50000})
    assert l.track == "VERIFY FIRST"


def test_complex_case_routes_to_premium():
    l = scoring.score_prospect({"property_id": "1", "name": "ESTATE OF A", "amount": 200000,
                                "eligibility_reviewed": True, "email": "e"})
    assert l.segment == "ESTATE" and l.track.startswith("PREMIUM")


def test_small_eligible_owner_is_self_serve():
    l = scoring.score_prospect({"property_id": "1", "name": "Tiny Owner", "amount": 200,
                                "eligibility_reviewed": True, "email": "e"})
    assert l.track == "SELF-SERVE NUDGE"


def test_clean_eligible_owner_is_fast_track():
    l = scoring.score_prospect({"property_id": "1", "name": "Jane Owner", "amount": 8000,
                                "eligibility_reviewed": True, "phone": "p", "email": "e"})
    assert l.track == "FAST TRACK"


def test_expected_fee_never_exceeds_ten_percent():
    # Even the most certain case can't imply more than the fee cap on the amount.
    l = scoring.score_prospect({"property_id": "1", "name": "X", "amount": 100000,
                                "eligibility_reviewed": True, "phone": "p", "email": "e"})
    assert l.expected_fee <= 100000 * 0.10


def test_prioritize_ranks_by_expected_fee():
    ps = [
        {"property_id": "small", "name": "Small", "amount": 5000,
         "eligibility_reviewed": True, "email": "e"},
        {"property_id": "big", "name": "Big Estate", "amount": 250000,
         "eligibility_reviewed": True, "email": "e"},
    ]
    ranked = scoring.prioritize(ps)
    assert ranked[0]["property_id"] == "big"       # bigger collectible fee leads


def test_value_priority_favors_sweet_spot_over_megaclaims():
    # A right-sized claim should out-prioritize a whale on the value component,
    # because huge balances come with barriers and shouldn't keep buying priority.
    sweet = scoring._value_priority(30000)
    mega = scoring._value_priority(2_000_000)
    assert sweet > mega


def test_barrier_score_estate_high_owner_zero():
    assert scoring.barrier_score({"amount": 5000}, "OWNER") == 0.0
    assert scoring.barrier_score({"amount": 300000}, "ESTATE") > 0.6


def test_reachability_uses_findability_when_no_contact():
    # No phone/email → score derives from how findable the person is.
    easy = scoring._reachability({"name": "Zephyrina Qubill", "last_known_address": "1 A St, Madison, WI 53703"})[0]
    hard = scoring._reachability({"name": "John Smith", "last_known_address": "Milwaukee, WI"})[0]
    assert easy > hard


def test_clean_midsize_outranks_barriered_whale():
    clean = {"property_id": "c", "name": "Jane Clean", "amount": 22000, "holder": "US BANK",
             "property_type": "Checking", "eligibility_reviewed": True,
             "last_known_address": "5 Elm St, Waunakee, WI 53597"}
    whale = {"property_id": "w", "name": "ESTATE OF J SMITH", "amount": 300000,
             "holder": "METLIFE", "property_type": "Insurance Proceeds",
             "eligibility_reviewed": True, "last_known_address": "1 Main St, Madison, WI 53703"}
    ranked = scoring.prioritize([whale, clean])
    assert ranked[0]["property_id"] == "c"     # achievable win leads
