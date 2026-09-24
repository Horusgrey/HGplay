"""Shared fixtures: a throwaway CRM backed by a temp DB per test."""
import pytest

from heirbud_crm import HeirBudCRM


@pytest.fixture
def crm(tmp_path):
    return HeirBudCRM(db_path=tmp_path / "test.db")


@pytest.fixture
def eligible_prospect(crm):
    """An imported, verified-eligible, human-reviewed prospect."""
    crm.add_prospect({"property_id": "T-ELIG", "name": "Eligible Test",
                      "amount": 100000, "holder": "EXAMPLE BANK",
                      "last_known_address": "1 Test St, Madison, WI"})
    crm.set_eligibility("T-ELIG", "2000-01-01", reviewed=True, reviewer="test",
                        evidence="unit-test fixture")
    return crm.get_prospect("T-ELIG")
