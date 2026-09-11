"""
payment_module.py — Close the money loop: invoice, gently remind, reconcile.

The pipeline gets a claim to PAID (the state pays the OWNER). This module handles
the last mile — the owner paying YOUR agreed fee — with the ethics baked in:

  • A fee is invoiced ONLY after the claimant has received their money.
  • CONTRACT mode → a clear invoice for the agreed, capped fee.
  • GRATUITY mode → a warm thank-you note. No invoice, no chase, no obligation —
    a voluntary tip, exactly as promised. (This is the whole point of that model.)
  • Reminders are friendly and finite: at most a few, then the record is flagged
    for a human, never badgered.
  • Nothing here touches SSNs, bank details, or the state claim itself.

Realized fees (the only real money) flow from here into the analytics value
ladder once a fee is marked paid.
"""
from pathlib import Path
from datetime import datetime, date

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

import compliance

INVOICE_DIR = Path(__file__).parent / "invoices"
INK = HexColor("#1a1814")
DIM = HexColor("#6b6459")
GREEN = HexColor("#1a5c2a")

# Reminder cadence in days AFTER the claimant confirms they received funds.
REMINDER_DAYS = [7, 21, 45]
MAX_REMINDERS = 3

# Fill in before real use. How claimants pay your fee.
PAY_CONFIG = {
    "business": "ZGroup LLC",
    "your_name": "[Your Name]",
    "contact": "[Your phone] · [Your email]",
    "methods": {
        "Venmo": "@your-venmo",
        "PayPal": "you@example.com",
        "Zelle": "(555) 555-5555",
        "Check": "ZGroup LLC, PO Box 000, City, WI",
    },
}


def _days_since(iso: str) -> int:
    try:
        return (datetime.now() - datetime.fromisoformat(iso)).days
    except (ValueError, TypeError):
        return -1


# ── Lifecycle transitions ────────────────────────────────────────────────────
def record_funds_received(crm, property_id: str, on: str = None) -> bool:
    """Mark that the CLAIMANT received their money from the state → stage PAID.

    This is the trigger that makes a fee invoice permissible. Nothing bills before it.
    """
    p = crm.get_prospect(property_id)
    if not p:
        return False
    when = on or datetime.now().isoformat()
    crm.update_prospect(property_id, funds_received_date=when)
    if p["stage"] not in ("SUPPRESSED", "CLOSED"):
        crm.update_stage(property_id, "PAID", "Claimant received funds from state")
    crm.log_contact_attempt(property_id, "System", "Funds Received",
                            "Claimant confirmed receipt of state payment")
    return True


def mark_fee_paid(crm, property_id: str, on: str = None) -> bool:
    """Record that the claimant paid your fee → stage CLOSED. Realized revenue."""
    p = crm.get_prospect(property_id)
    if not p:
        return False
    when = on or datetime.now().isoformat()
    crm.update_prospect(property_id, fee_paid=1, fee_paid_date=when)
    fee = compliance.fee_amount(p.get("amount", 0))
    crm.log_contact_attempt(property_id, "System", "Fee Paid", f"Fee ${fee:,.2f} received — closed")
    if p["stage"] != "SUPPRESSED":
        crm.update_stage(property_id, "CLOSED", "Fee paid — record closed")
    return True


# ── Invoice / thank-you document ─────────────────────────────────────────────
def _draw_doc(prospect: dict, mode: str, output_dir) -> str:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() else "_" for c in prospect.get("name", "Unknown"))
    kind = "ThankYou" if mode == "GRATUITY" else "Invoice"
    path = output_dir / f"{kind}_{safe}.pdf"

    amount = float(prospect.get("amount", 0))
    fee = compliance.fee_amount(amount)
    fn = (prospect.get("name") or "there").split(" ")[0]
    c = canvas.Canvas(str(path), pagesize=letter)
    W, H = letter
    M = 1.0 * inch
    y = H - M

    c.setFillColor(INK); c.setFont("Times-Bold", 15)
    c.drawString(M, y, PAY_CONFIG["business"])
    c.setFont("Helvetica", 8.5); c.setFillColor(DIM)
    c.drawString(M, y - 13, "Wisconsin unclaimed-property assistance")
    c.drawRightString(W - M, y, datetime.now().strftime("%B %d, %Y"))
    y -= 42

    c.setFillColor(INK)
    if mode == "GRATUITY":
        c.setFont("Helvetica-Bold", 13)
        c.drawString(M, y, "A note of thanks"); y -= 26
        lines = [
            f"Hi {fn},",
            "",
            "Wonderful news that your unclaimed property came through — I'm genuinely happy",
            "you got what was yours. It was my pleasure to help.",
            "",
            "There's no bill here and nothing you owe. If you'd like to send a thank-you of",
            "your own choosing, it's always appreciated — but never expected. Either way, I'm",
            "glad it worked out for you.",
            "",
            "If a friend or family member ever needs a hand with something like this, I'm happy",
            "to help them too.",
        ]
        c.setFont("Helvetica", 10.5)
        for ln in lines:
            c.drawString(M, y, ln); y -= 15
        y -= 6
        if any(PAY_CONFIG["methods"].values()):
            c.setFont("Helvetica-Oblique", 9); c.setFillColor(DIM)
            c.drawString(M, y, "Should you wish to: "
                         + " · ".join(f"{k} {v}" for k, v in PAY_CONFIG["methods"].items() if v))
            y -= 20
    else:
        c.setFont("Helvetica-Bold", 13)
        c.drawString(M, y, "FEE INVOICE"); y -= 8
        c.setFont("Helvetica", 8.5); c.setFillColor(DIM)
        c.drawRightString(W - M, y + 8, f"Re: {prospect.get('property_id','')}")
        y -= 20
        c.setFillColor(INK); c.setFont("Helvetica", 10.5)
        for ln in [f"Billed to: {prospect.get('name','')}", ""]:
            c.drawString(M, y, ln); y -= 15
        # amount box
        c.setFont("Helvetica", 10.5); c.setFillColor(DIM)
        c.drawString(M, y, "Property recovered from the State of Wisconsin")
        c.setFillColor(INK); c.drawRightString(W - M, y, f"${amount:,.2f}"); y -= 18
        c.setFillColor(DIM); c.drawString(M, y, "Agreed locator fee (10% — the Wisconsin maximum)")
        c.setFillColor(GREEN); c.setFont("Helvetica-Bold", 12)
        c.drawRightString(W - M, y, f"${fee:,.2f}"); y -= 26
        c.setFont("Helvetica", 10)
        body = [
            "This is the fee we agreed in writing, now due because you have received your",
            "funds. As promised, there was no upfront cost and nothing was owed unless you",
            "were paid — which you now have been. Thank you for trusting me with this.",
            "",
            "Payment options:",
        ]
        for ln in body:
            c.drawString(M, y, ln); y -= 15
        for k, v in PAY_CONFIG["methods"].items():
            if v:
                c.drawString(M + 14, y, f"• {k}: {v}"); y -= 14
        y -= 8
        c.setFont("Helvetica-Oblique", 9); c.setFillColor(DIM)
        c.drawString(M, y, "No rush, and thank you again. — " + PAY_CONFIG["your_name"])

    # footer
    c.setFont("Helvetica", 7.5); c.setFillColor(DIM)
    c.drawCentredString(W / 2, 0.7 * inch,
                        f"{PAY_CONFIG['business']} · {PAY_CONFIG['contact']} · "
                        "a private locator service, not the State of Wisconsin")
    c.save()
    return str(path)


def generate_invoice(crm, property_id: str) -> dict:
    """Create the invoice (contract) or thank-you (gratuity). Requires funds received."""
    p = crm.get_prospect(property_id)
    if not p:
        return {"error": "not found"}
    if not p.get("funds_received_date"):
        return {"error": "Claimant has not received funds yet — cannot invoice a fee."}
    mode = (p.get("fee_model") or "CONTRACT").upper()
    path = _draw_doc(p, mode, INVOICE_DIR)
    crm.update_prospect(property_id, fee_invoiced=1, fee_invoice_date=datetime.now().isoformat())
    label = "Thank-you note" if mode == "GRATUITY" else "Invoice"
    crm.log_contact_attempt(property_id, "System", "Fee Invoiced", f"{label} generated ({mode})")
    return {"success": True, "mode": mode, "kind": label, "path": path}


# ── Reminders (contract only, friendly & finite) ─────────────────────────────
def reminder_text(prospect: dict, n: int) -> str:
    fn = (prospect.get("name") or "there").split(" ")[0]
    fee = compliance.fee_amount(prospect.get("amount", 0))
    if n == 1:
        return (f"Hi {fn}, just a gentle note — whenever it's convenient, the agreed "
                f"${fee:,.2f} locator fee is ready to settle. No rush at all, and thanks again "
                f"for letting me help.")
    if n == 2:
        return (f"Hi {fn}, floating this back up in case it slipped by — the agreed "
                f"${fee:,.2f} fee for recovering your property. Happy to take it however's "
                f"easiest for you. Thank you!")
    return (f"Hi {fn}, last friendly note from me on the agreed ${fee:,.2f} fee. If now's not "
            f"a good time just let me know — I won't keep nudging. Grateful either way.")


def reminders_due(crm) -> list:
    """Contract records that received funds, were invoiced, unpaid, and are due a nudge."""
    out = []
    for p in crm.get_all_prospects():
        if (p.get("fee_model") or "CONTRACT").upper() != "CONTRACT":
            continue                      # gratuity is never chased
        if not p.get("funds_received_date") or p.get("fee_paid") or not p.get("fee_invoiced"):
            continue
        sent = int(p.get("fee_reminders_sent") or 0)
        if sent >= MAX_REMINDERS:
            continue
        days = _days_since(p["funds_received_date"])
        if days >= REMINDER_DAYS[min(sent, len(REMINDER_DAYS) - 1)]:
            out.append({"property_id": p["property_id"], "name": p["name"],
                        "amount": p["amount"], "fee": compliance.fee_amount(p["amount"]),
                        "reminder_number": sent + 1, "days_since_funds": days,
                        "message": reminder_text(p, sent + 1)})
    out.sort(key=lambda x: -x["fee"])
    return out


def log_reminder_sent(crm, property_id: str) -> bool:
    p = crm.get_prospect(property_id)
    if not p:
        return False
    crm.update_prospect(property_id,
                        fee_reminders_sent=int(p.get("fee_reminders_sent") or 0) + 1,
                        fee_last_reminder=datetime.now().isoformat())
    return True


# ── Collections dashboard ────────────────────────────────────────────────────
def dashboard(crm) -> dict:
    ps = crm.get_all_prospects()
    to_invoice, awaiting_fee, collected = [], [], 0.0
    for p in ps:
        fee = compliance.fee_amount(p.get("amount", 0))
        if p.get("fee_paid"):
            collected += fee
        elif p.get("funds_received_date") and not p.get("fee_invoiced"):
            to_invoice.append({"property_id": p["property_id"], "name": p["name"],
                               "amount": p["amount"], "fee": fee,
                               "mode": (p.get("fee_model") or "CONTRACT").upper()})
        elif p.get("fee_invoiced") and not p.get("fee_paid"):
            awaiting_fee.append({"property_id": p["property_id"], "name": p["name"],
                                 "fee": fee, "mode": (p.get("fee_model") or "CONTRACT").upper()})
    return {
        "collected_fees": round(collected, 2),
        "to_invoice": to_invoice,
        "awaiting_fee": awaiting_fee,
        "reminders_due": reminders_due(crm),
    }


if __name__ == "__main__":
    import tempfile, os
    from heirbud_crm import HeirBudCRM
    db = os.path.join(tempfile.mkdtemp(), "pay.db")
    crm = HeirBudCRM(db_path=db)
    crm.add_prospect({"property_id": "C1", "name": "Dana Contract", "amount": 18450,
                      "fee_model": "CONTRACT", "eligibility_reviewed": True})
    crm.add_prospect({"property_id": "G1", "name": "Gina Gratuity", "amount": 640,
                      "fee_model": "GRATUITY", "eligibility_reviewed": True})
    for pid in ("C1", "G1"):
        record_funds_received(crm, pid)
        print(generate_invoice(crm, pid))
    print("dashboard:", {k: (v if not isinstance(v, list) else len(v)) for k, v in dashboard(crm).items()})
