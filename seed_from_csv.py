"""
seed_from_csv.py — Load WI Priority Targets CSV into the HeirBud CRM.

Usage:
    python seed_from_csv.py --file WI_HeirFinder_Priority_Targets.csv --min-amount 50000
    python seed_from_csv.py --file targets.csv --min-amount 25000 --max-rows 500
"""
import argparse
import csv
import hashlib
import sys
import urllib.parse
from heirbud_crm import HeirBudCRM


def deterministic_id(name: str, address: str) -> str:
    """Stable fallback ID when the source lacks a property ID.

    Uses a SHA-1 of normalized fields so the SAME record always yields the
    SAME id across runs and machines — Python's built-in hash() is
    process-randomized and produced a different id every run, defeating
    deduplication (flagged in the PRJ-HB7K4 audit).
    """
    key = f"{(name or '').strip().lower()}|{(address or '').strip().lower()}"
    return "GEN-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12].upper()

# Column aliases — handles variations across WI exports
COL_MAP = {
    "property_id": ["property id", "propertyid", "prop id", "id"],
    "last_name": ["lastname", "last name", "last"],
    "first_name": ["firstname", "first name", "first"],
    "name": ["name", "owner name", "owner"],
    "amount": ["amount", "reported value", "value", "cash amount"],
    "property_type": ["property type", "propertytype", "type"],
    "holder": ["holder", "holder name", "reported by"],
    "address": ["address", "street", "last known address"],
    "city": ["city"],
    "state": ["state", "st"],
    "zip": ["zip", "zipcode", "zip code"],
}


def find_col(headers: list[str], key: str) -> str | None:
    aliases = COL_MAP.get(key, [key])
    for h in headers:
        if h.lower().strip() in aliases:
            return h
    return None


def build_search_urls(name: str, city: str) -> dict:
    n_dash = name.replace(" ", "-")
    n_und = name.replace(" ", "_")
    n_enc = urllib.parse.quote(name)
    c_enc = urllib.parse.quote(f"{city} WI" if city else "WI")
    return {
        "whitepages": f"https://www.whitepages.com/name/{n_dash}/WI",
        "truepeoplesearch": f"https://www.truepeoplesearch.com/results?name={n_enc}&citystatezip={c_enc}",
        "fastpeoplesearch": f"https://www.fastpeoplesearch.com/name/{n_und}_WI",
    }


def parse_amount(raw: str) -> float:
    try:
        return float(str(raw).replace("$", "").replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def seed(file: str, min_amount: float, max_rows: int, priority_only: bool) -> dict:
    crm = HeirBudCRM()
    added, skipped, filtered = 0, 0, 0

    with open(file, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        cols = {k: find_col(headers, k) for k in COL_MAP}

        rows = []
        for row in reader:
            amount = parse_amount(row.get(cols["amount"] or "", 0))
            if amount < min_amount:
                filtered += 1
                continue

            if cols["name"] and row.get(cols["name"]):
                name = row[cols["name"]].strip()
            else:
                first = row.get(cols["first_name"] or "", "").strip()
                last = row.get(cols["last_name"] or "", "").strip()
                name = f"{first} {last}".strip()
            if not name:
                filtered += 1
                continue

            city = row.get(cols["city"] or "", "").strip()
            addr_parts = [row.get(cols["address"] or "", "").strip(), city,
                          row.get(cols["state"] or "", "WI").strip() or "WI",
                          row.get(cols["zip"] or "", "").strip()]
            address = ", ".join(p for p in addr_parts if p)

            priority = "HIGH" if amount > 100000 else "MEDIUM" if amount > 25000 else "LOW"
            if priority_only and priority != "HIGH":
                filtered += 1
                continue

            rows.append({
                "property_id": row.get(cols["property_id"] or "", "") or deterministic_id(name, address),
                "name": name,
                "last_known_address": address,
                "amount": amount,
                "property_type": row.get(cols["property_type"] or "", "").strip(),
                "holder": row.get(cols["holder"] or "", "").strip(),
                "priority": priority,
                "search_urls": build_search_urls(name, city),
            })

        # Highest value first, cap at max_rows
        rows.sort(key=lambda r: r["amount"], reverse=True)
        for r in rows[:max_rows]:
            if crm.add_prospect(r):
                added += 1
            else:
                skipped += 1

    return {"added": added, "skipped_duplicates": skipped, "filtered_out": filtered}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Seed HeirBud CRM from WI unclaimed property CSV")
    ap.add_argument("--file", required=True, help="Path to CSV file")
    ap.add_argument("--min-amount", type=float, default=50000, help="Minimum claim amount (default 50000)")
    ap.add_argument("--max-rows", type=int, default=500, help="Max prospects to import (default 500)")
    ap.add_argument("--high-only", action="store_true", help="Only import HIGH priority (>$100k)")
    args = ap.parse_args()

    try:
        result = seed(args.file, args.min_amount, args.max_rows, args.high_only)
    except FileNotFoundError:
        sys.exit(f"File not found: {args.file}")

    print(f"✓ Added {result['added']} prospects")
    print(f"  Skipped {result['skipped_duplicates']} duplicates")
    print(f"  Filtered {result['filtered_out']} below threshold")
