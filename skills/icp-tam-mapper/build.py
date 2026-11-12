"""Orchestrator: icp.json → ICP Matrix XLSX + AI Ark filters + TAM/SAM/SOM breakdown.

Usage:
    python3 build.py <icp.json> [output_dir]

Produces, in output_dir (default: alongside the icp.json):
    {Company}_ICP_Matrix.xlsx           — the 5-sheet ICP matrix (+ per-sheet CSVs)
    {company}-airk-filters.json         — exact AI Ark filter JSON (paste-ready)
    {Company}_TAM_Breakdown.md          — TAM/SAM/SOM + personas + Clay signals

The icp.json is authored by the research step (Claude, or generate_icp.py). It has
two blocks: `matrix` (drives the XLSX) and `airk` (drives the AI Ark funnel). See
icp_schema.json.
"""
from __future__ import annotations

import os
import sys
import json

import icp_matrix
import airk


def run(icp_path: str, out_dir: str | None = None) -> dict:
    with open(icp_path, "r", encoding="utf-8") as f:
        icp = json.load(f)

    company = icp.get("company_name") or "Company"
    out_dir = out_dir or os.path.dirname(os.path.abspath(icp_path))
    os.makedirs(out_dir, exist_ok=True)
    safe = company.replace(" ", "_").replace("/", "-").replace("(", "").replace(")", "")
    slug = company.lower().replace(" ", "-").replace("/", "-").replace("(", "").replace(")", "")

    # 1) ICP Matrix XLSX (+ CSVs)
    matrix = icp.get("matrix", {})
    matrix.setdefault("key_signal_name", icp.get("key_signal_name", "Key Signal"))
    xlsx_path = icp_matrix.build_xlsx(matrix, company, out_dir)
    print(f"✓ ICP Matrix XLSX     → {xlsx_path}")

    # 2) AI Ark filters + live counts
    spec = icp.get("airk", {})
    # carry the signal narrative through for the breakdown's Clay section
    spec.setdefault("key_signal", icp.get("key_signal", ""))
    spec.setdefault("intent_signal", icp.get("intent_signal", ""))
    spec.setdefault("clay_signals", icp.get("clay_signals", []))
    filters = airk.build_filters(spec)

    filters_path = os.path.join(out_dir, f"{slug}-airk-filters.json")
    with open(filters_path, "w", encoding="utf-8") as f:
        json.dump({
            "icp_type": filters["icp_type"],
            "company_filters": filters["company"],
            "people_filters_base_account": filters["sam_base"],
            "personas": {p["label"]: p["filter"] for p in filters["personas"]},
        }, f, indent=2)
    print(f"✓ AI Ark filter JSON  → {filters_path}")

    print("  Running live AI Ark counts…")
    results = airk.run_counts(filters)
    comp = results["company"]
    print(f"    TAM={comp.get('TAM')}  SAM={comp.get('SAM')}  SOM={comp.get('SOM')}")
    for p in results["people"]:
        print(f"    {p['label']}: {p['count']}")

    # 3) Breakdown markdown
    md = airk.breakdown_markdown(company, spec, filters, results)
    md_path = os.path.join(out_dir, f"{safe}_TAM_Breakdown.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"✓ TAM breakdown doc   → {md_path}")

    return {"xlsx": xlsx_path, "filters": filters_path, "breakdown": md_path,
            "results": results}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
