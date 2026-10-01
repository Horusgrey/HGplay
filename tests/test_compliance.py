"""Lock the compliance rule pack. If any of these break, revenue is at legal risk."""
import compliance


def test_fee_cap_clamps_over_cap_whole_percent():
    assert compliance.cap_fee_pct(20) == 10.0
    assert compliance.cap_fee_pct(15) == 10.0
    assert compliance.cap_fee_pct(100) == 10.0


def test_fee_cap_accepts_fraction_form():
    assert compliance.cap_fee_pct(0.10) == 10.0
    assert compliance.cap_fee_pct(0.05) == 5.0   # under cap stays under


def test_fee_cap_allows_under_cap():
    assert compliance.cap_fee_pct(7) == 7.0


def test_default_fee_is_the_cap():
    assert compliance.compliant_fee_pct() == 10.0


def test_fee_amount_uses_cap_even_when_over_requested():
    # 20% requested on $100k must still bill 10% = $10k
    assert compliance.fee_amount(100000, 20) == 10000.0


def test_eligibility_requires_verified_custody_date():
    v = compliance.check_eligibility(None)
    assert not v.eligible


def test_eligibility_blocks_under_24_months():
    # A very recent custody date is always ineligible.
    v = compliance.check_eligibility("2099-01-01")  # future-ish -> definitely < 24mo
    assert not v.eligible


def test_eligibility_allows_old_custody():
    v = compliance.check_eligibility("2000-01-01")
    assert v.eligible
    assert v.custody_months >= compliance.CUSTODY_MONTHS_REQUIRED


def test_assert_agreement_allowed_blocks_ineligible():
    import pytest
    with pytest.raises(compliance.EligibilityError):
        compliance.assert_agreement_allowed({"custody_date": None})


def test_assert_agreement_allowed_blocks_unreviewed_even_if_old():
    import pytest
    with pytest.raises(compliance.EligibilityError):
        compliance.assert_agreement_allowed({"custody_date": "2000-01-01"})  # no review flag


def test_assert_agreement_allowed_passes_when_eligible_and_reviewed():
    elig = compliance.assert_agreement_allowed(
        {"custody_date": "2000-01-01", "eligibility_reviewed": True})
    assert elig.eligible


def test_disclosure_names_the_free_state_path_and_denies_gov_identity():
    d = compliance.FREE_CLAIM_DISCLOSURE.lower()
    assert "no cost" in d or "free" in d
    assert compliance.STATE_PORTAL in compliance.FREE_CLAIM_DISCLOSURE
    assert "not the state" in d


# ── Outreach states: softer than the agreement gate, and never a substitute ──
def test_presumed_from_report_date_when_not_yet_verified():
    state, why = compliance.eligibility_state({"report_date": "2019-01-01"})
    assert state == compliance.PRESUMED
    assert "confirm" in why.lower()


def test_presumed_never_unlocks_an_agreement():
    import pytest
    p = {"report_date": "2019-01-01"}
    assert compliance.eligibility_state(p)[0] == compliance.PRESUMED
    with pytest.raises(compliance.EligibilityError):
        compliance.assert_agreement_allowed(p)


def test_verified_requires_both_review_and_a_date():
    assert compliance.eligibility_state(
        {"custody_date": "2000-01-01", "eligibility_reviewed": True})[0] == compliance.VERIFIED
    # reviewed flag alone, with no date, is not verification
    assert compliance.eligibility_state({"eligibility_reviewed": True})[0] == compliance.UNKNOWN


def test_recent_report_date_is_too_recent_not_presumed():
    from datetime import date
    assert compliance.eligibility_state(
        {"report_date": "2025-01-01"}, as_of=date(2026, 1, 1))[0] == compliance.TOO_RECENT


def test_unreadable_and_missing_dates_are_unknown():
    assert compliance.eligibility_state({})[0] == compliance.UNKNOWN
    assert compliance.eligibility_state({"report_date": "sometime in the 90s"})[0] == compliance.UNKNOWN


def test_suppression_beats_every_other_state():
    p = {"custody_date": "2000-01-01", "eligibility_reviewed": True,
         "suppression_status": "SUPPRESSED"}
    assert compliance.eligibility_state(p)[0] == compliance.SUPPRESSED
    assert compliance.may_send_letter(p, "GRATUITY") is False
    assert compliance.may_send_letter(p, "CONTRACT") is False


def test_gratuity_may_send_on_presumed_but_contract_may_not():
    p = {"report_date": "2019-01-01"}
    assert compliance.may_send_letter(p, "GRATUITY") is True
    assert compliance.may_send_letter(p, "CONTRACT") is False


def test_contract_may_send_once_verified():
    p = {"custody_date": "2000-01-01", "eligibility_reviewed": True}
    assert compliance.may_send_letter(p, "CONTRACT") is True


def test_gratuity_may_send_even_with_no_date_at_all():
    # Telling someone their money exists is lawful whatever the custody clock says.
    assert compliance.may_send_letter({}, "GRATUITY") is True
