"""
heirbud_server.py — FastAPI backend for the HeirBud dashboard.

Run:
    pip install fastapi uvicorn reportlab
    uvicorn heirbud_server:app --reload --port 8001
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import os
import csv
import io

from heirbud_crm import HeirBudCRM, STAGES
from outreach_generator import generate_scripts, SuppressedProspectError
from contract_generator import generate_contract
from followup_engine import build_action_queue
from seed_from_csv import build_search_urls, parse_amount, find_col, COL_MAP, deterministic_id
import compliance

app = FastAPI(title="HeirBud API", version="2.1")

# CORS + auth are configurable via env so the default is not wide-open.
# HEIRBUD_ORIGINS: comma-separated allowlist (default: localhost dev only).
# HEIRBUD_API_KEY: if set, every mutating endpoint requires X-API-Key.
_origins = os.environ.get("HEIRBUD_ORIGINS", "http://localhost,http://127.0.0.1").split(",")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in _origins if o.strip()],
                   allow_methods=["*"], allow_headers=["*"])

API_KEY = os.environ.get("HEIRBUD_API_KEY")


def require_key(x_api_key: str | None = Header(default=None)):
    """Dependency: enforce X-API-Key when HEIRBUD_API_KEY is configured.

    NOTE: This is a minimal gate for a single-operator prototype, not a full
    auth system. The PRJ-HB7K4 audit requires real authentication, roles, and
    audit logging before production. See AUTONOMOUS_SYSTEM.md.
    """
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(401, "Missing or invalid X-API-Key")


crm = HeirBudCRM()


# ── MODELS ──
class ProspectIn(BaseModel):
    property_id: str
    name: str
    last_known_address: str = ""
    amount: float = 0
    property_type: str = ""
    holder: str = ""
    priority: str = "MEDIUM"
    stage: str = "IDENTIFIED"
    phone: str | None = None
    email: str | None = None
    notes: str = ""


class StageUpdate(BaseModel):
    property_id: str
    stage: str
    notes: str = ""


class ContactLog(BaseModel):
    property_id: str
    method: str
    outcome: str
    notes: str = ""


class OutreachReq(BaseModel):
    property_id: str


class ContractReq(BaseModel):
    property_id: str
    fee_pct: float | None = None   # None → compliant default; any value is capped


class ContactUpdate(BaseModel):
    property_id: str
    phone: str | None = None
    email: str | None = None


class EligibilityReq(BaseModel):
    property_id: str
    custody_date: str              # verified DOR custody date (ISO or year)
    reviewed: bool = False         # True once a human confirms the state record
    reviewer: str = ""


class SuppressReq(BaseModel):
    property_id: str
    reason: str = ""


# ── ENDPOINTS ──
@app.get("/health")
def health():
    s = crm.get_pipeline_summary()
    return {"status": "ok", "prospect_count": s["total_prospects"],
            "pipeline_value": s["total_pipeline_value"]}


@app.get("/prospects")
def list_prospects(stage: str | None = None, min_amount: float | None = None):
    return {"prospects": crm.get_all_prospects(stage=stage, min_amount=min_amount)}


@app.get("/prospects/{property_id}")
def get_prospect(property_id: str):
    p = crm.get_prospect(property_id)
    if not p:
        raise HTTPException(404, "Prospect not found")
    return p


@app.post("/prospects")
def add_prospect(p: ProspectIn, _=Depends(require_key)):
    d = p.model_dump()
    city = d["last_known_address"].split(",")[1].strip() if "," in d["last_known_address"] else ""
    d["search_urls"] = build_search_urls(d["name"], city)
    if not crm.add_prospect(d):
        raise HTTPException(409, "Prospect already exists")
    return {"success": True, "property_id": d["property_id"]}


@app.post("/prospects/contact")
def update_contact(u: ContactUpdate, _=Depends(require_key)):
    fields = {}
    if u.phone is not None:
        fields["phone"] = u.phone
    if u.email is not None:
        fields["email"] = u.email
    if not crm.update_prospect(u.property_id, **fields):
        raise HTTPException(404, "Prospect not found")
    # Auto-advance to ENRICHED if contact info added
    p = crm.get_prospect(u.property_id)
    if (p["phone"] or p["email"]) and p["stage"] == "IDENTIFIED":
        crm.update_stage(u.property_id, "ENRICHED", "Auto: contact info added")
    return {"success": True}


@app.post("/seed/csv")
async def seed_csv(file: UploadFile = File(...), min_amount: float = 50000, max_rows: int = 500,
                   _=Depends(require_key)):
    """Upload the WI CSV directly — server-side import."""
    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    headers = reader.fieldnames or []
    cols = {k: find_col(headers, k) for k in COL_MAP}

    rows = []
    for row in reader:
        amount = parse_amount(row.get(cols["amount"] or "", 0))
        if amount < min_amount:
            continue
        if cols["name"] and row.get(cols["name"]):
            name = row[cols["name"]].strip()
        else:
            name = f'{row.get(cols["first_name"] or "", "").strip()} {row.get(cols["last_name"] or "", "").strip()}'.strip()
        if not name:
            continue
        city = row.get(cols["city"] or "", "").strip()
        address = ", ".join(p for p in [row.get(cols["address"] or "", "").strip(), city,
                                        row.get(cols["state"] or "", "WI").strip() or "WI",
                                        row.get(cols["zip"] or "", "").strip()] if p)
        rows.append({
            "property_id": row.get(cols["property_id"] or "", "") or deterministic_id(name, address),
            "name": name, "last_known_address": address, "amount": amount,
            "property_type": row.get(cols["property_type"] or "", "").strip(),
            "holder": row.get(cols["holder"] or "", "").strip(),
            "priority": "HIGH" if amount > 100000 else "MEDIUM" if amount > 25000 else "LOW",
            "search_urls": build_search_urls(name, city),
        })

    rows.sort(key=lambda r: r["amount"], reverse=True)
    added = sum(1 for r in rows[:max_rows] if crm.add_prospect(r))
    return {"added": added, "skipped": len(rows[:max_rows]) - added, "total_candidates": len(rows)}


@app.post("/outreach/generate")
def outreach(req: OutreachReq):
    p = crm.get_prospect(req.property_id)
    if not p:
        raise HTTPException(404, "Prospect not found")
    try:
        return generate_scripts(p)
    except SuppressedProspectError as e:
        raise HTTPException(409, str(e))


@app.post("/crm/eligibility")
def set_eligibility(req: EligibilityReq, _=Depends(require_key)):
    """Record a verified custody date and (optionally) mark it human-reviewed."""
    verdict = crm.set_eligibility(req.property_id, req.custody_date,
                                  reviewed=req.reviewed, reviewer=req.reviewer)
    if verdict is None:
        raise HTTPException(404, "Prospect not found")
    return {"success": True, "eligibility": verdict}


@app.post("/crm/suppress")
def suppress(req: SuppressReq, _=Depends(require_key)):
    """Opt a record out of all future outreach (terminal)."""
    if not crm.suppress(req.property_id, req.reason):
        raise HTTPException(404, "Prospect not found")
    return {"success": True}


@app.post("/contract/generate")
def contract(req: ContractReq, _=Depends(require_key)):
    p = crm.get_prospect(req.property_id)
    if not p:
        raise HTTPException(404, "Prospect not found")
    try:
        path = generate_contract(p, fee_pct=req.fee_pct)
    except compliance.EligibilityError as e:
        # 422: the record is not eligible for a (non-void) agreement yet.
        raise HTTPException(422, f"Not eligible for an agreement: {e}")
    used_pct = compliance.cap_fee_pct(req.fee_pct) if req.fee_pct is not None else compliance.compliant_fee_pct()
    crm.log_contact_attempt(req.property_id, "System", "Agreement Sent",
                            f"Contract PDF generated ({used_pct:.0f}%)")
    return {"success": True, "path": path, "fee_pct": used_pct,
            "download": f"/contract/download/{p['property_id']}"}


@app.get("/contract/download/{property_id}")
def download_contract(property_id: str):
    p = crm.get_prospect(property_id)
    if not p:
        raise HTTPException(404, "Prospect not found")
    safe_name = "".join(c if c.isalnum() else "_" for c in p["name"])
    path = Path(__file__).parent / "contracts" / f"ZGroup_Agreement_{safe_name}.pdf"
    if not path.exists():
        raise HTTPException(404, "Contract not generated yet — POST /contract/generate first")
    return FileResponse(str(path), media_type="application/pdf", filename=path.name)


@app.post("/crm/update_stage")
def update_stage(u: StageUpdate, _=Depends(require_key)):
    if u.stage not in STAGES:
        raise HTTPException(400, f"Invalid stage. Must be one of {STAGES}")
    if not crm.update_stage(u.property_id, u.stage, u.notes):
        raise HTTPException(404, "Prospect not found")
    return {"success": True}


@app.post("/crm/log_contact")
def log_contact(l: ContactLog, _=Depends(require_key)):
    if not crm.log_contact_attempt(l.property_id, l.method, l.outcome, l.notes):
        raise HTTPException(404, "Prospect not found")
    return {"success": True}


@app.get("/pipeline/summary")
def pipeline_summary():
    return crm.get_pipeline_summary()


@app.get("/actions/today")
def todays_actions():
    """The autonomy endpoint — prioritized daily action queue."""
    return {"actions": build_action_queue(crm)}
