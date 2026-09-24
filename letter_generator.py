"""
letter_generator.py — Physical, USPS-ready outreach letters as one-page PDFs.

Two modes, both honest, both lead with the free state path:

  GRATUITY — the model that inspired this whole thing. A warm note: "I found
             this, here's how to claim it free, and if it works out a thank-you
             of your choosing is appreciated but never expected." No contract,
             no obligation. Lowest friction, highest trust, best for smaller
             claims and goodwill/referrals.

  CONTRACT — the professional option: same honest free-path disclosure, plus an
             offer to handle the paperwork on a capped, in-writing, only-if-paid
             contingency. An agreement is enclosed (see contract_generator).

The mode is chosen per prospect (see scoring.recommended_mode) or set globally.
USPS-first is deliberate: a real letter to the last-known address establishes
legitimacy and creates a clean record before any digital contact.
"""
import os
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

import compliance

OUTPUT_DIR = Path(__file__).parent / "letters"

# Where the owner portal lives. Set HEIRBUD_BASE_URL to your real domain before
# mailing (e.g. https://claim.yourdomain.com). The QR on each letter points at
# that owner's private verification page.
BASE_URL = os.environ.get("HEIRBUD_BASE_URL", "http://localhost:8001")
INK = HexColor("#1a1814")
DIM = HexColor("#6b6459")
ACCENT = HexColor("#1a5c2a")

# Fill these in with your real details before mailing.
SENDER = {
    "name": "[Your Name]",
    "org": "ZGroup LLC",
    "line": "Wisconsin unclaimed-property assistance",
    "address": "[Your return address]",
    "contact": "[Your phone] · [Your email]",
}


def verify_url(prospect: dict) -> str | None:
    """The owner's private verification link. None if there's no record id."""
    pid = prospect.get("property_id")
    return f"{BASE_URL}/verify?id={quote(str(pid))}" if pid else None


def _draw_qr(c, url: str, x: float, y: float, size: float):
    """Draw a QR code for `url` at (x, y) with side length `size`. Pure reportlab."""
    qr = QrCodeWidget(url)
    b = qr.getBounds()
    w, h = b[2] - b[0], b[3] - b[1]
    d = Drawing(size, size, transform=[size / w, 0, 0, size / h, -b[0] * size / w, -b[1] * size / h])
    d.add(qr)
    renderPDF.draw(d, c, x, y)


def _wrap(text: str, width: int = 92) -> list[str]:
    out, line = [], ""
    for word in text.split():
        if len(line) + len(word) + 1 > width:
            out.append(line); line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        out.append(line)
    return out


def _body_paragraphs(prospect: dict, mode: str) -> list[str]:
    fn = (prospect.get("name") or "there").split(" ")[0]
    amount = float(prospect.get("amount", 0))
    holder = prospect.get("holder") or "a past account"
    amt = f"${amount:,.0f}"
    fee = compliance.compliant_fee_pct()

    common_open = (
        f"I came across your name while researching Wisconsin unclaimed-property "
        f"records, and it looks like the State of Wisconsin is holding about {amt} "
        f"that belongs to you — originally from {holder}. I'm writing to let you know, "
        f"because most people never find out.")
    free_line = (
        f"First, the honest part: this is your money, and you can claim it yourself "
        f"for free, directly from the state, at {compliance.STATE_PORTAL} or by calling "
        f"{compliance.STATE_PHONE}. You do not need me or anyone else to get it.")
    not_gov = ("I'm a private individual who helps people find and claim what's theirs — "
               "I am not the State of Wisconsin or any government agency.")

    if mode == "GRATUITY":
        offer = (
            "If the paperwork feels like a hassle, I'm glad to walk you through it at no "
            "cost. If it works out and you'd like to send a thank-you of your own choosing "
            "afterward, that's always appreciated — but never expected and never required. "
            "Either way, I hope you get what's yours.")
    else:  # CONTRACT
        offer = (
            f"If you'd rather I handle the paperwork and filing for you, I offer that on a "
            f"simple contingency basis: a {fee:.0f}% fee (the maximum Wisconsin allows), agreed "
            f"in writing first, and owed only if you're actually paid — no upfront cost, cancel "
            f"anytime. I've enclosed a one-page agreement you can read over. There's no "
            f"obligation, and claiming it yourself for free is always an option.")

    vurl = verify_url(prospect)
    if vurl:
        close = ("Prefer to check online right now? Scan the code at the top of this letter "
                 "to see your record and your options on a secure page — or reach out using "
                 "the details below and I'll send you the exact state record.")
    else:
        close = ("To confirm this is really yours, I can send you the exact state record. "
                 "Just reach out using the details below.")
    return [common_open, free_line, not_gov, offer, close]


def letter_text(prospect: dict, mode: str = "CONTRACT") -> str:
    """The full plain-text letter — greeting, body, sign-off, disclosure.

    This is the single source of the letter's words; generate_letter() just
    lays this out on a page. Exposed so the content is testable without a PDF.
    """
    mode = (mode or "CONTRACT").upper()
    if mode not in ("CONTRACT", "GRATUITY"):
        raise ValueError("mode must be CONTRACT or GRATUITY")
    fn = (prospect.get("name") or "there").split(" ")[0]
    close = "Warmly," if mode == "GRATUITY" else "Sincerely,"
    parts = [f"Dear {fn},", ""]
    parts += _body_paragraphs(prospect, mode)
    parts += ["", close, SENDER["name"], f"{SENDER['org']} · {SENDER['contact']}",
              "", compliance.FREE_CLAIM_DISCLOSURE]
    return "\n\n".join(parts)


def generate_letter(prospect: dict, mode: str = "CONTRACT", output_dir=OUTPUT_DIR) -> str:
    """Render a one-page letter PDF; returns the path. mode: CONTRACT | GRATUITY."""
    mode = (mode or "CONTRACT").upper()
    if mode not in ("CONTRACT", "GRATUITY"):
        raise ValueError("mode must be CONTRACT or GRATUITY")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() else "_" for c in prospect.get("name", "Unknown"))
    path = output_dir / f"Letter_{mode.title()}_{safe}.pdf"

    c = canvas.Canvas(str(path), pagesize=letter)
    W, H = letter
    M = 1.0 * inch
    y = H - M

    # Sender letterhead
    c.setFillColor(INK); c.setFont("Times-Bold", 15)
    c.drawString(M, y, SENDER["org"])
    c.setFont("Helvetica", 8.5); c.setFillColor(DIM)
    c.drawString(M, y - 13, SENDER["line"])
    c.drawRightString(W - M, y, datetime.now().strftime("%B %d, %Y"))

    # QR → the owner's private verification page (physical letter → digital trust).
    vurl = verify_url(prospect)
    if vurl:
        qsize = 0.95 * inch
        _draw_qr(c, vurl, W - M - qsize, y - 13 - qsize, qsize)
        c.setFont("Helvetica", 6.8); c.setFillColor(DIM)
        c.drawRightString(W - M, y - 13 - qsize - 9, "Scan to verify your record")
        y -= (qsize + 4)
    y -= 40

    # Recipient
    c.setFillColor(INK); c.setFont("Helvetica", 10.5)
    c.drawString(M, y, prospect.get("name", ""))
    for part in [p.strip() for p in (prospect.get("last_known_address") or "").split(",")]:
        if part:
            y -= 13; c.drawString(M, y, part)
    y -= 30

    fn = (prospect.get("name") or "there").split(" ")[0]
    c.setFont("Helvetica", 10.5)
    c.drawString(M, y, f"Dear {fn},")
    y -= 22

    for para in _body_paragraphs(prospect, mode):
        for line in _wrap(para):
            c.drawString(M, y, line); y -= 14
        y -= 8

    y -= 6
    c.drawString(M, y, "Warmly," if mode == "GRATUITY" else "Sincerely,")
    y -= 26
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(M, y, SENDER["name"])
    y -= 14
    c.setFont("Helvetica", 9.5); c.setFillColor(DIM)
    c.drawString(M, y, f"{SENDER['org']} · {SENDER['contact']}")

    # Footer disclosure — always present, both modes
    c.setFont("Helvetica-Oblique", 7.5)
    for i, line in enumerate(_wrap(compliance.FREE_CLAIM_DISCLOSURE, 110)):
        c.drawString(M, 0.7 * inch - i * 9, line)

    c.save()
    return str(path)


if __name__ == "__main__":
    demo = {"name": "Jordan Sample", "amount": 4200,
            "last_known_address": "1 Test St, Madison, WI 53703",
            "holder": "US BANK NA"}
    print("Gratuity:", generate_letter(demo, "GRATUITY"))
    print("Contract:", generate_letter(demo, "CONTRACT"))
