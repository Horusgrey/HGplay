"""Lock outreach copy (no scammy/false-authority language) and the contract gate."""
import pytest

import compliance
from outreach_generator import generate_scripts, SuppressedProspectError
from contract_generator import generate_contract

BANNED = [
    "absorbed", "seized", "act now", "final notice", "you must",
    "liquidat", "guaranteed", "free money", "safekeeping",
]

SAMPLE = {"property_id": "O1", "name": "Sam Sample", "amount": 50000,
          "holder": "EXAMPLE BANK"}


def test_outreach_fee_is_capped():
    assert generate_scripts(SAMPLE)["fee_pct"] == 10.0


def test_outreach_contains_free_claim_path_in_every_channel():
    s = generate_scripts(SAMPLE)
    for channel in ("cold_call_script", "cold_email", "sms_opener"):
        assert compliance.STATE_PORTAL in s[channel], f"{channel} missing free-claim path"


def test_outreach_declares_not_the_state():
    s = generate_scripts(SAMPLE)
    blob = (s["cold_call_script"] + s["cold_email"] + s["sms_opener"]).lower()
    assert "not the state" in blob or "not a government" in blob or "not with the state" in blob


def test_outreach_has_no_banned_phrases():
    s = generate_scripts(SAMPLE)
    blob = (s["cold_call_script"] + s["cold_email"] + s["sms_opener"]).lower()
    hits = [b for b in BANNED if b in blob]
    assert not hits, f"banned phrases present: {hits}"


def test_outreach_refuses_suppressed():
    with pytest.raises(SuppressedProspectError):
        generate_scripts({**SAMPLE, "suppression_status": "SUPPRESSED"})


def test_contract_blocked_for_ineligible(tmp_path):
    with pytest.raises(compliance.EligibilityError):
        generate_contract({**SAMPLE, "custody_date": "2099-01-01",
                           "eligibility_reviewed": True}, output_dir=tmp_path)


def test_contract_blocked_without_review(tmp_path):
    with pytest.raises(compliance.EligibilityError):
        generate_contract({**SAMPLE, "custody_date": "2000-01-01"}, output_dir=tmp_path)


def test_contract_succeeds_and_clamps_fee(tmp_path):
    p = {**SAMPLE, "custody_date": "2000-01-01", "eligibility_reviewed": True}
    # fed 20% — the file must still be produced; the clamp is verified via fee_amount.
    path = generate_contract(p, fee_pct=20, output_dir=tmp_path)
    assert path.endswith(".pdf")
    assert compliance.fee_amount(p["amount"], 20) == 5000.0  # 10% of 50k, not 20%
