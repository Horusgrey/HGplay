"""Lock the analytics math — especially the four distinct dollar figures."""
import analytics


def _advance(crm, pid, *stages):
    for s in stages:
        crm.update_stage(pid, s, "test")


def test_value_ladder_keeps_figures_distinct(crm):
    # Two records; only one is eligible; none paid.
    crm.add_prospect({"property_id": "A", "name": "A", "amount": 100000})
    crm.add_prospect({"property_id": "B", "name": "B", "amount": 50000})
    crm.set_eligibility("A", "2000-01-01", reviewed=True, evidence="x")  # eligible
    vl = analytics.value_ladder(crm)
    assert vl["published_value"] == 150000
    assert vl["eligible_value"] == 100000            # only A
    assert vl["expected_fee"] == 10000               # 10% of eligible
    assert vl["realized_fee"] == 0                   # nothing paid yet


def test_realized_fee_only_counts_paid(crm):
    crm.add_prospect({"property_id": "A", "name": "A", "amount": 100000})
    crm.set_eligibility("A", "2000-01-01", reviewed=True, evidence="x")
    _advance(crm, "A", "ENRICHED", "CONTACTED", "RESPONDED", "AGREEMENT_SENT",
             "SIGNED", "FILED", "PAID")
    vl = analytics.value_ladder(crm)
    assert vl["realized_fee"] == 10000               # now 10% of the paid amount


def test_funnel_counts_reached_at_least_each_stage(crm):
    crm.add_prospect({"property_id": "A", "name": "A", "amount": 1})
    crm.add_prospect({"property_id": "B", "name": "B", "amount": 1})
    _advance(crm, "A", "ENRICHED", "CONTACTED")      # A reached CONTACTED
    # B stays IDENTIFIED
    fn = {r["stage"]: r["reached"] for r in analytics.funnel(crm)}
    assert fn["IDENTIFIED"] == 2
    assert fn["ENRICHED"] == 1
    assert fn["CONTACTED"] == 1
    assert fn["RESPONDED"] == 0


def test_suppressed_still_counts_for_stages_it_reached(crm):
    crm.add_prospect({"property_id": "A", "name": "A", "amount": 1})
    _advance(crm, "A", "ENRICHED", "CONTACTED")
    crm.suppress("A", "opt out")
    fn = {r["stage"]: r["reached"] for r in analytics.funnel(crm)}
    # It opted out, but it DID reach CONTACTED — the funnel must not erase that.
    assert fn["CONTACTED"] == 1


def test_compliance_metrics_rates(crm):
    for i in range(4):
        crm.add_prospect({"property_id": f"P{i}", "name": str(i), "amount": 1})
    crm.set_eligibility("P0", "2000-01-01", reviewed=True, evidence="x")
    crm.suppress("P1", "opt out")
    cm = analytics.compliance_metrics(crm)
    assert cm["total"] == 4
    assert cm["eligibility_verified"] == 1
    assert cm["suppressed"] == 1
    assert cm["suppression_rate_pct"] == 25.0


def test_narrative_is_plain_english_and_nonempty(crm):
    crm.add_prospect({"property_id": "A", "name": "A", "amount": 100000})
    crm.set_eligibility("A", "2000-01-01", reviewed=True, evidence="x")
    s = analytics.summary(crm)
    assert s["narrative"] and all(isinstance(x, str) and x for x in s["narrative"])
    # The money story must mention the reachable fee figure.
    assert any("reachable fee" in line for line in s["narrative"])
