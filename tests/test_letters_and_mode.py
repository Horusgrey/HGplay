"""Lock the letter generator and the contract/gratuity mode toggle."""
import pytest

import compliance
import scoring
import letter_generator as lg


def test_recommended_mode_small_is_gratuity():
    assert scoring.recommended_mode({"name": "Jo Owner", "amount": 500}) == "GRATUITY"


def test_recommended_mode_large_is_contract():
    assert scoring.recommended_mode({"name": "Jo Owner", "amount": 25000}) == "CONTRACT"


def test_recommended_mode_complex_always_contract_even_if_small():
    assert scoring.recommended_mode({"name": "ESTATE OF X", "amount": 100}) == "CONTRACT"


def test_explicit_fee_model_overrides_recommendation():
    lead = scoring.score_prospect({"property_id": "1", "name": "Jo", "amount": 50,
                                   "fee_model": "CONTRACT"})
    assert lead.mode == "CONTRACT"     # tiny → would recommend gratuity, but overridden


def test_gratuity_letter_has_no_fee_or_contract_language():
    p = {"name": "Marie W", "amount": 840, "holder": "WE ENERGIES"}
    txt = lg.letter_text(p, "GRATUITY").lower()
    assert "thank-you" in txt
    assert "10%" not in txt and "contingency" not in txt and "enclosed a\none-page" not in txt


def test_contract_letter_states_capped_fee_and_agreement():
    p = {"name": "Dan B", "amount": 18450, "holder": "SCHWAB"}
    txt = lg.letter_text(p, "CONTRACT")
    assert "10%" in txt and "agreement" in txt.lower()


def test_every_letter_leads_with_free_path_and_denies_gov_identity():
    for mode in ("GRATUITY", "CONTRACT"):
        txt = lg.letter_text({"name": "X Y", "amount": 1000, "holder": "H"}, mode)
        assert compliance.STATE_PORTAL in txt
        assert "not the State of Wisconsin" in txt
        assert "for free" in txt.lower()


def test_invalid_mode_rejected():
    with pytest.raises(ValueError):
        lg.letter_text({"name": "X"}, "SHARKY")


def test_verify_url_built_from_property_id(monkeypatch):
    monkeypatch.setattr(lg, "BASE_URL", "https://claim.example")
    assert lg.verify_url({"property_id": "WI-1"}) == "https://claim.example/verify?id=WI-1"
    assert lg.verify_url({"name": "no id"}) is None


def test_letter_invites_scan_when_record_has_id():
    txt = lg.letter_text({"name": "Dan", "amount": 5000, "property_id": "WI-9"}, "CONTRACT")
    assert "scan the code" in txt.lower()



def test_generate_letter_writes_pdf(tmp_path):
    path = lg.generate_letter({"name": "Test P", "amount": 500, "holder": "H",
                               "last_known_address": "1 A St, Madison, WI"},
                              "GRATUITY", output_dir=tmp_path)
    assert path.endswith(".pdf")
    from pathlib import Path
    assert Path(path).exists() and Path(path).stat().st_size > 500
