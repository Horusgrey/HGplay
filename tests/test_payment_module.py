"""Lock the money loop: invoice only after funds, mode-aware docs, friendly finite reminders."""
import payment_module as pay
import compliance


def _paid_prospect(crm, pid="C1", mode="CONTRACT", amount=20000):
    crm.add_prospect({"property_id": pid, "name": f"{mode} Person", "amount": amount,
                      "fee_model": mode, "eligibility_reviewed": True})
    return crm.get_prospect(pid)


def test_cannot_invoice_before_funds_received(crm, tmp_path):
    _paid_prospect(crm)
    pay.INVOICE_DIR = tmp_path
    res = pay.generate_invoice(crm, "C1")
    assert res.get("error") and "funds" in res["error"]


def test_invoice_after_funds_received(crm, tmp_path):
    _paid_prospect(crm)
    pay.INVOICE_DIR = tmp_path
    pay.record_funds_received(crm, "C1")
    res = pay.generate_invoice(crm, "C1")
    assert res["success"] and res["kind"] == "Invoice"
    assert crm.get_prospect("C1")["fee_invoiced"] is True


def test_gratuity_produces_thankyou_not_invoice(crm, tmp_path):
    _paid_prospect(crm, pid="G1", mode="GRATUITY", amount=600)
    pay.INVOICE_DIR = tmp_path
    pay.record_funds_received(crm, "G1")
    res = pay.generate_invoice(crm, "G1")
    assert res["kind"] == "Thank-you note"


def test_gratuity_is_never_in_reminders(crm):
    _paid_prospect(crm, pid="G1", mode="GRATUITY", amount=600)
    pay.record_funds_received(crm, "G1", on="2000-01-01T00:00:00")   # long overdue
    crm.update_prospect("G1", fee_invoiced=1)
    assert pay.reminders_due(crm) == []          # gratuity is a gift, never chased


def test_contract_reminder_becomes_due_and_is_finite(crm):
    _paid_prospect(crm)
    pay.record_funds_received(crm, "C1", on="2000-01-01T00:00:00")
    crm.update_prospect("C1", fee_invoiced=1)
    due = pay.reminders_due(crm)
    assert due and due[0]["reminder_number"] == 1
    # exhaust reminders → stops (never badgers)
    crm.update_prospect("C1", fee_reminders_sent=pay.MAX_REMINDERS)
    assert pay.reminders_due(crm) == []


def test_mark_fee_paid_closes_and_counts_as_realized(crm):
    _paid_prospect(crm, amount=20000)
    pay.record_funds_received(crm, "C1")
    pay.mark_fee_paid(crm, "C1")
    p = crm.get_prospect("C1")
    assert p["fee_paid"] is True and p["stage"] == "CLOSED"
    d = pay.dashboard(crm)
    assert d["collected_fees"] == compliance.fee_amount(20000)


def test_realized_fee_in_analytics_reflects_collected(crm):
    import analytics
    _paid_prospect(crm, amount=50000)
    pay.record_funds_received(crm, "C1")
    assert analytics.value_ladder(crm)["realized_fee"] == 0     # invoiced-not-paid = not realized
    pay.mark_fee_paid(crm, "C1")
    assert analytics.value_ladder(crm)["realized_fee"] == compliance.fee_amount(50000)
