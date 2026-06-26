"""
contract_generator.py — Generate one-page contingency agreement PDFs.
Output: ZGroup_Agreement_{ProspectName}.pdf
"""
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

OUTPUT_DIR = Path(__file__).parent / "contracts"

INK = HexColor("#1a1814")
DIM = HexColor("#7a7060")
GREEN = HexColor("#1a5c2a")
LINE = HexColor("#c8c0b0")


def generate_contract(prospect: dict, fee_pct: int = 15, output_dir=OUTPUT_DIR) -> str:
    """Generate the PDF; returns the file path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c if c.isalnum() else "_" for c in prospect.get("name", "Unknown"))
    path = output_dir / f"ZGroup_Agreement_{safe_name}.pdf"

    c = canvas.Canvas(str(path), pagesize=letter)
    W, H = letter
    M = 0.9 * inch
    y = H - M

    # ── Letterhead ──
    c.setFillColor(INK)
    c.setFont("Times-BoldItalic", 26)
    c.drawString(M, y, "ZGroup LLC")
    c.setFont("Helvetica", 8)
    c.setFillColor(DIM)
    c.drawString(M, y - 14, "WISCONSIN ASSET LOCATOR SERVICES")
    c.drawRightString(W - M, y, datetime.now().strftime("%B %d, %Y"))
    y -= 30
    c.setStrokeColor(INK)
    c.setLineWidth(1.5)
    c.line(M, y, W - M, y)
    y -= 28

    # ── Title ──
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(W / 2, y, "ASSET RECOVERY CONTINGENCY AGREEMENT")
    y -= 30

    # ── Claimant block ──
    def field(label, value, yy):
        c.setFont("Helvetica", 7.5)
        c.setFillColor(DIM)
        c.drawString(M, yy, label.upper())
        c.setFont("Helvetica", 10.5)
        c.setFillColor(INK)
        c.drawString(M, yy - 13, str(value or "—"))
        return yy - 32

    y = field("Claimant", prospect.get("name"), y)
    y = field("Last Known Address", prospect.get("last_known_address"), y)

    half = (W - 2 * M) / 2
    yy = y
    c.setFont("Helvetica", 7.5); c.setFillColor(DIM)
    c.drawString(M, yy, "PROPERTY ID")
    c.drawString(M + half, yy, "ORIGINAL HOLDER")
    c.setFont("Helvetica", 10.5); c.setFillColor(INK)
    c.drawString(M, yy - 13, str(prospect.get("property_id", "—")))
    holder = str(prospect.get("holder", "—"))
    c.drawString(M + half, yy - 13, holder[:42])
    y = yy - 32

    yy = y
    c.setFont("Helvetica", 7.5); c.setFillColor(DIM)
    c.drawString(M, yy, "PROPERTY TYPE")
    c.drawString(M + half, yy, "ESTIMATED VALUE")
    c.setFont("Helvetica", 10.5); c.setFillColor(INK)
    c.drawString(M, yy - 13, str(prospect.get("property_type", "—"))[:42])
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(GREEN)
    amount = float(prospect.get("amount", 0))
    c.drawString(M + half, yy - 14, f"${amount:,.2f}")
    y = yy - 38

    c.setStrokeColor(LINE)
    c.setLineWidth(0.75)
    c.line(M, y, W - M, y)
    y -= 22

    # ── Terms ──
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(M, y, "TERMS OF ENGAGEMENT")
    y -= 18

    fee_amount = amount * fee_pct / 100
    terms = [
        f"1. ZGroup LLC (\"Locator\") agrees to assist the Claimant in recovering the above-referenced",
        f"    unclaimed property from the Wisconsin Department of Revenue Unclaimed Property Division,",
        f"    including preparation and filing of all required claim forms, affidavits, and supporting",
        f"    documentation, and all follow-up correspondence with the state treasury.",
        "",
        f"2. CONTINGENCY FEE: Locator's fee shall be {fee_pct}% of the gross recovered amount",
        f"    (estimated fee: ${fee_amount:,.2f}), due and payable ONLY upon successful recovery and",
        f"    receipt of funds by the Claimant. If no recovery is made, no fee is owed.",
        "",
        f"3. NO UPFRONT COST: Claimant shall owe nothing under any circumstances prior to recovery.",
        "",
        f"4. RIGHT TO SELF-FILE: Claimant acknowledges they retain the right to claim this property",
        f"    directly through the State of Wisconsin at no cost, and enters this agreement to engage",
        f"    Locator's services voluntarily for convenience and expertise.",
        "",
        f"5. TERMINATION: Claimant may terminate this agreement in writing at any time prior to the",
        f"    filing of the claim with the state.",
    ]
    c.setFont("Helvetica", 9)
    for line in terms:
        c.drawString(M, y, line)
        y -= 12.5

    y -= 18
    c.setStrokeColor(LINE)
    c.line(M, y, W - M, y)
    y -= 36

    # ── Signatures ──
    sig_w = (W - 2 * M - 40) / 2
    c.setStrokeColor(INK)
    c.setLineWidth(0.75)
    c.line(M, y, M + sig_w, y)
    c.line(M + sig_w + 40, y, W - M, y)
    c.setFont("Helvetica", 7.5)
    c.setFillColor(DIM)
    c.drawString(M, y - 11, "CLAIMANT SIGNATURE")
    c.drawString(M + sig_w + 40, y - 11, "ZGROUP REPRESENTATIVE")
    y -= 40
    c.line(M, y, M + sig_w * 0.6, y)
    c.line(M + sig_w + 40, y, M + sig_w + 40 + sig_w * 0.6, y)
    c.drawString(M, y - 11, "DATE")
    c.drawString(M + sig_w + 40, y - 11, "DATE")

    # ── Footer ──
    c.setFont("Helvetica", 7)
    c.setFillColor(DIM)
    c.drawCentredString(W / 2, 0.55 * inch,
                        "ZGroup LLC · Wisconsin Asset Locator · This agreement is governed by the laws of the State of Wisconsin")

    c.save()
    return str(path)


if __name__ == "__main__":
    demo = {"property_id": "8476391", "name": "John Hoover",
            "last_known_address": "560 White Oak Cir, Hudson, WI 54016",
            "amount": 283265.10, "property_type": "Misc. Outstanding Checks",
            "holder": "COINBASE INC"}
    print("Generated:", generate_contract(demo, fee_pct=12))
