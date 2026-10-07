"""Lock the CRM-level gates: eligibility evidence, suppression, dedupe, migration."""
import pytest

import compliance
from seed_from_csv import deterministic_id


def test_deterministic_id_stable():
    a = deterministic_id("Jane Doe", "1 Main St")
    b = deterministic_id("Jane Doe", "1 Main St")
    assert a == b and a.startswith("GEN-")


def test_deterministic_id_normalizes_case_and_space():
    assert deterministic_id("  Jane DOE ", "1 MAIN st") == deterministic_id("jane doe", "1 main st")


def test_add_prospect_dedupes_on_property_id(crm):
    p = {"property_id": "D1", "name": "Dup"}
    assert crm.add_prospect(p) is True
    assert crm.add_prospect(p) is False   # second insert rejected


def test_set_eligibility_requires_evidence_when_reviewed(crm):
    crm.add_prospect({"property_id": "E1", "name": "NoEvidence"})
    with pytest.raises(ValueError):
        crm.set_eligibility("E1", "2000-01-01", reviewed=True)   # no evidence


def test_set_eligibility_reviewed_only_when_eligible(crm):
    crm.add_prospect({"property_id": "E2", "name": "Recent"})
    v = crm.set_eligibility("E2", "2099-01-01", reviewed=True, evidence="x")
    assert v["eligible"] is False
    assert crm.get_prospect("E2")["eligibility_reviewed"] is False  # not flagged


def test_suppress_is_terminal_and_blocks_auto_advance(crm):
    crm.add_prospect({"property_id": "S1", "name": "OptOut"})
    crm.suppress("S1", "asked to stop")
    p = crm.get_prospect("S1")
    assert p["stage"] == "SUPPRESSED"
    assert p["suppression_status"] == "SUPPRESSED"
    # A later "Replied" outcome must NOT resurrect it.
    crm.log_contact_attempt("S1", "Email", "Replied", "late reply")
    assert crm.get_prospect("S1")["stage"] == "SUPPRESSED"


def test_needs_custody_verification_excludes_verified_and_suppressed(crm, eligible_prospect):
    crm.add_prospect({"property_id": "V1", "name": "Unverified", "amount": 5000})
    crm.add_prospect({"property_id": "V2", "name": "Suppressed", "amount": 5000})
    crm.suppress("V2")
    ids = {r["property_id"] for r in crm.needs_custody_verification()}
    assert "V1" in ids            # unverified -> on the worklist
    assert "T-ELIG" not in ids    # verified eligible -> off the worklist
    assert "V2" not in ids        # suppressed -> off the worklist


def test_compliance_columns_migrate_onto_v1_db(tmp_path):
    """A pre-existing DB without compliance columns must gain them on open."""
    import sqlite3
    dbp = tmp_path / "legacy.db"
    con = sqlite3.connect(dbp)
    # The true pre-compliance (v1) schema — no compliance columns yet.
    con.execute("""CREATE TABLE prospects (
        property_id TEXT PRIMARY KEY, name TEXT NOT NULL, last_known_address TEXT,
        amount REAL DEFAULT 0, property_type TEXT, holder TEXT,
        priority TEXT DEFAULT 'MEDIUM', stage TEXT DEFAULT 'IDENTIFIED',
        phone TEXT, email TEXT, notes TEXT DEFAULT '', search_urls TEXT DEFAULT '{}',
        created_at TEXT, updated_at TEXT)""")
    con.commit(); con.close()
    from heirbud_crm import HeirBudCRM
    crm = HeirBudCRM(db_path=dbp)               # should ALTER in new columns
    crm.add_prospect({"property_id": "L1", "name": "Legacy", "amount": 1})
    v = crm.set_eligibility("L1", "2000-01-01", reviewed=True, evidence="ok")
    assert v["eligible"] is True
