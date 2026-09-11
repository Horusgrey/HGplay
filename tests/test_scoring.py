"""Lock the prioritization logic — the 'high dollar ≠ high priority' principle."""
import scoring


def test_segment_classification():
    assert scoring.segment({"name": "ESTATE OF J. SMITH"}) == "ESTATE"
    assert scoring.segment({"name": "The Doe Family Trust"}) == "TRUST"
    assert scoring.segment({"name": "Acme LLC"}) == "BUSINESS"
    assert scoring.segment({"name": "Jane Q. Public"}) == "OWNER"


def test_institutional_claimants_are_business_not_people():
    # Wisconsin's list is not all individuals. These are real shapes from the
    # state file; treating them as people would put them in "households" and
    # send them heir letters.
    for org in ["US BANK NA", "SUMMIT CREDIT UNION", "AURORA HEALTH CARE",
                "STATE OF WISCONSIN", "FOND DU LAC COUNTY", "CITY OF MADISON",
                "ST MARYS HOSPITAL", "MADISON AREA TECHNICAL COLLEGE",
                "FIRST BAPTIST CHURCH", "ACME HOLDINGS", "TEAMSTERS LOCAL 344"]:
        assert scoring.segment({"name": org}) == "BUSINESS", org


def test_ordinary_people_are_still_owners():
    for person in ["Jane Q. Public", "Gokhan Kiyak", "Mary Spies",
                   "Eudora Keeton", "Michael Hershberger"]:
        assert scoring.segment({"name": person}) == "OWNER", person


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


def test_multi_claim_person_outranks_an_equal_single_claim():
    # Same money, same profile — but one conversation closes three claims, so it
    # is worth more of the operator's day. This is the household leverage rule.
    addr = "2210 Sherman Ave, Madison, WI, 53704"
    multi = [{"property_id": f"M{i}", "name": "Michael Hershberger", "amount": 8000,
              "eligibility_reviewed": True, "last_known_address": addr,
              "city": "Madison", "zip": "53704"} for i in range(3)]
    solo = {"property_id": "S", "name": "Wanda Onlyclaim", "amount": 8000,
            "eligibility_reviewed": True, "last_known_address": "9 Oak St, Madison, WI, 53703",
            "city": "Madison", "zip": "53703"}
    ranked = scoring.prioritize(multi + [solo])
    assert ranked[0]["name"] == "Michael Hershberger"
    assert ranked[0]["claims"] == 3
    assert "one letter covers all" in ranked[0]["reason"]
    assert next(l for l in ranked if l["property_id"] == "S")["claims"] == 1


def test_leverage_never_resurrects_a_suppressed_record():
    addr = "1 Elm St, Madison, WI, 53703"
    ps = [{"property_id": f"X{i}", "name": "Opted Out", "amount": 50000,
           "suppression_status": "SUPPRESSED", "eligibility_reviewed": True,
           "last_known_address": addr, "city": "Madison", "zip": "53703"} for i in range(4)]
    assert all(l["score"] == 0.0 for l in scoring.prioritize(ps))


def test_clean_midsize_outranks_barriered_whale():
    clean = {"property_id": "c", "name": "Jane Clean", "amount": 22000, "holder": "US BANK",
             "property_type": "Checking", "eligibility_reviewed": True,
             "last_known_address": "5 Elm St, Waunakee, WI 53597"}
    whale = {"property_id": "w", "name": "ESTATE OF J SMITH", "amount": 300000,
             "holder": "METLIFE", "property_type": "Insurance Proceeds",
             "eligibility_reviewed": True, "last_known_address": "1 Main St, Madison, WI 53703"}
    ranked = scoring.prioritize([whale, clean])
    assert ranked[0]["property_id"] == "c"     # achievable win leads
