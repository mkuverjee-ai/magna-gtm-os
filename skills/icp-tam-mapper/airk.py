"""AI Ark engine: ICP spec → filters → live TAM/SAM/SOM counts → breakdown markdown.

Mirrors the production copy-bot/tam_intake.py filter shapes. READ-ONLY: only POSTs
to AI Ark's /companies and /people SEARCH endpoints (return counts + profiles).

The ICP `airk` spec (see icp_schema.json) drives everything:
  icp_type            "firmographic" | "signal_defined" | "hybrid"
  geographies         full country names (all target geos)          → TAM location
  priority_geographies subset explicitly prioritized                → SAM/SOM location
  industries          AI Ark industry strings (broad)               → TAM industries
  priority_industries subset (core)                                 → SAM/SOM industries
  keyword_terms       "what they do" gate (hybrid/signal_defined)   → SAM/SOM keyword include
  keyword_exclude     disqualifier phrases                          → SAM/SOM keyword exclude
  employee_min/max    overall size band                             → employeeSize
  sweet_spot          [min,max] best-fit size band                  → SOM size
  revenue_floor       USD floor or null                             → SOM revenue (optional)
  personas            [{label, titles[], seniorities[], department?}] → people counts
"""
from __future__ import annotations

import json
import sys
import ssl
import subprocess
import urllib.request
import urllib.error

from config import (AI_ARK_API_KEY, AI_ARK_BASE, AI_ARK_UA, KEYWORD_SOURCES)


# ── HTTP (urllib, with curl fallback for old-Python TLS) ──────────────────────

def _headers():
    if not AI_ARK_API_KEY:
        sys.exit("No AI_ARK_API_KEY. Add it with: python3 gtm.py set-key AI_ARK_API_KEY")
    return {
        "X-TOKEN": AI_ARK_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": AI_ARK_UA,
    }


def _post(path: str, body: dict) -> dict:
    url = f"{AI_ARK_BASE}/{path}"
    payload = json.dumps(body).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=payload, headers=_headers(), method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except (ssl.SSLError, urllib.error.URLError, urllib.error.HTTPError):
        # Old system-Python TLS gets rejected by the AI Ark edge — fall back to curl.
        args = ["curl", "-s", "-X", "POST", url]
        for k, v in _headers().items():
            args += ["-H", f"{k}: {v}"]
        args += ["--data-binary", json.dumps(body)]
        out = subprocess.run(args, capture_output=True, text=True, timeout=90)
        return json.loads(out.stdout)


def count(path: str, body: dict) -> int | None:
    """Return totalElements for a size:1 search, or None on error."""
    body = {**body, "page": 0, "size": 1}
    try:
        data = _post(path, body)
    except Exception:
        return None
    n = data.get("totalElements") if isinstance(data, dict) else None
    return n if isinstance(n, int) else None


# ── Filter builders ───────────────────────────────────────────────────────────

def account(geo, emp_min, emp_max, industries=None, keyword_terms=None,
            keyword_exclude=None, revenue_floor=None) -> dict:
    """Build an AI Ark company (`account`) filter."""
    a = {
        "location": {"any": {"include": geo}},
        "employeeSize": {"type": "RANGE", "range": [{"start": emp_min, "end": emp_max}]},
    }
    if industries:
        a["industries"] = {"any": {"include": {"mode": "SMART", "content": industries}}}
    if keyword_terms:
        block = {"include": {"sources": KEYWORD_SOURCES, "content": keyword_terms}}
        if keyword_exclude:
            # exclude MUST use the same {sources, content} shape as include — a bare array 400s.
            block["exclude"] = {"sources": KEYWORD_SOURCES, "content": keyword_exclude}
        a["keyword"] = {"any": block}
    if revenue_floor:
        a["revenue"] = {"type": "RANGE", "range": [{"start": int(revenue_floor), "end": 100000000000}]}
    return a


def contact(titles, seniorities, department=None) -> dict:
    """Build an AI Ark people (`contact`) filter for a persona."""
    c = {
        "seniority": {"any": {"include": seniorities}},
        "experience": {"current": {"title": {"any": {"include": {"mode": "SMART", "content": titles}}}}},
    }
    if department:
        c["department"] = {"any": {"include": [department]}}
    return c


# ── The funnel ────────────────────────────────────────────────────────────────

def build_filters(spec: dict) -> dict:
    """ICP airk spec → {TAM, SAM, SOM} account filters + persona contact filters."""
    geo_all = spec.get("geographies") or ["United States"]
    geo_pri = spec.get("priority_geographies") or geo_all
    ind_all = spec.get("industries") or []
    ind_pri = spec.get("priority_industries") or ind_all
    kw = spec.get("keyword_terms") or []
    kw_excl = spec.get("keyword_exclude") or []
    emp_min = int(spec.get("employee_min") or 10)
    emp_max = int(spec.get("employee_max") or 50000)
    ss = spec.get("sweet_spot") or [emp_min, emp_max]
    rev = spec.get("revenue_floor")
    icp_type = spec.get("icp_type", "firmographic")

    signal = icp_type in ("signal_defined", "hybrid") and bool(kw)

    # TAM — broadest defensible market: all geos, full size band, broad industries.
    tam = account(geo_all, emp_min, emp_max, industries=(ind_all or None))

    # SAM — priority geos + the core "what they are" gate.
    if icp_type == "signal_defined":
        sam = account(geo_pri, emp_min, emp_max, keyword_terms=kw, keyword_exclude=kw_excl)
    elif icp_type == "hybrid":
        sam = account(geo_pri, emp_min, emp_max, industries=(ind_pri or None),
                      keyword_terms=kw, keyword_exclude=kw_excl)
    else:  # firmographic
        sam = account(geo_pri, emp_min, emp_max, industries=(ind_pri or None))

    # SOM — SAM narrowed to the sweet-spot size band (+ optional revenue floor).
    if icp_type == "signal_defined":
        som = account(geo_pri, ss[0], ss[1], keyword_terms=kw, keyword_exclude=kw_excl, revenue_floor=rev)
    elif icp_type == "hybrid":
        som = account(geo_pri, ss[0], ss[1], industries=(ind_pri or None),
                      keyword_terms=kw, keyword_exclude=kw_excl, revenue_floor=rev)
    else:
        som = account(geo_pri, ss[0], ss[1], industries=(ind_pri or None), revenue_floor=rev)

    personas = []
    for p in spec.get("personas", []):
        personas.append({
            "label": p.get("label", ""),
            "filter": contact(p.get("titles", []), p.get("seniorities", []), p.get("department")),
        })

    return {
        "icp_type": icp_type,
        "signal_defined": signal,
        "geo_all": geo_all, "geo_pri": geo_pri,
        "emp_min": emp_min, "emp_max": emp_max, "sweet_spot": ss,
        "company": {"TAM": tam, "SAM": sam, "SOM": som},
        "sam_base": sam,
        "personas": personas,
    }


def run_counts(filters: dict) -> dict:
    """Execute live AI Ark counts for the company funnel + personas."""
    comp = {}
    for seg in ("TAM", "SAM", "SOM"):
        comp[seg] = count("companies", {"account": filters["company"][seg]})
    people = []
    for p in filters["personas"]:
        n = count("people", {"account": filters["sam_base"], "contact": p["filter"]})
        people.append({"label": p["label"], "count": n})
    return {"company": comp, "people": people}


# ── Breakdown markdown ────────────────────────────────────────────────────────

def _fmt(n):
    return f"{n:,}" if isinstance(n, int) else "—"


def _pct(n, tam):
    if not isinstance(n, int) or not isinstance(tam, int) or tam <= 0:
        return ""
    p = 100.0 * n / tam
    return f" (~{p:.1f}% of TAM)" if p >= 0.1 else " (<0.1% of TAM)"


def breakdown_markdown(company_name: str, spec: dict, filters: dict, results: dict) -> str:
    comp = results["company"]
    tam_n = comp.get("TAM")
    geo_all = filters["geo_all"]; geo_pri = filters["geo_pri"]
    ss = filters["sweet_spot"]; emp_min = filters["emp_min"]; emp_max = filters["emp_max"]
    kind = {"signal_defined": "signal-defined", "hybrid": "hybrid (industry + keyword gate)"}.get(
        filters["icp_type"], "firmographic")

    L = []
    L.append(f"# {company_name} — AI Ark TAM / SAM / SOM Breakdown")
    L.append("")
    L.append(f"_ICP type: **{kind}** · counts pulled live from AI Ark (69M+ companies, 400M+ people)._")
    L.append("")
    L.append("## 📊 Market funnel (companies)")
    L.append("")
    L.append("| Segment | Definition | Companies |")
    L.append("|---|---|---|")
    L.append(f"| **TAM** | {len(geo_all)} geos · broad verticals · {emp_min:,}–{emp_max:,} emp | **{_fmt(comp.get('TAM'))}** |")
    L.append(f"| **SAM** | {len(geo_pri)} priority geos · core gate | **{_fmt(comp.get('SAM'))}**{_pct(comp.get('SAM'), tam_n)} |")
    L.append(f"| **SOM** | SAM · sweet-spot {ss[0]:,}–{ss[1]:,} emp | **{_fmt(comp.get('SOM'))}**{_pct(comp.get('SOM'), tam_n)} |")
    L.append("")
    if results["people"]:
        L.append("## 👤 Buyers within SAM")
        L.append("")
        L.append("| Persona | Contacts |")
        L.append("|---|---|")
        for p in results["people"]:
            L.append(f"| {p['label']} | **{_fmt(p['count'])}** |")
        L.append("")
        L.append("_Personas overlap — do not sum them._")
        L.append("")

    ksig = (spec.get("key_signal") or "").strip()
    isig = (spec.get("intent_signal") or "").strip()
    L.append("## ⚠️ What AI Ark can't filter — layer in Clay")
    L.append("")
    L.append("These are the ICP's Key Qualifying Signal + Intent rows; AI Ark can't see them, so enrich in Clay after the pull:")
    L.append("")
    if ksig:
        L.append(f"- **Key qualifying signal:** {ksig}")
    if isig:
        L.append(f"- **Intent signal:** {isig}")
    for extra in spec.get("clay_signals", []):
        L.append(f"- {extra}")
    L.append("")
    L.append("## 🎯 Filters used")
    L.append("")
    L.append("**Geographies (all):** " + ", ".join(geo_all))
    L.append("")
    L.append("**Priority geographies:** " + ", ".join(geo_pri))
    L.append("")
    if spec.get("keyword_terms"):
        L.append("**Keyword gate (KEYWORD + DESCRIPTION + SEO):** " + ", ".join(spec["keyword_terms"]))
        L.append("")
    if spec.get("keyword_exclude"):
        L.append("**Keyword exclude:** " + ", ".join(spec["keyword_exclude"]))
        L.append("")
    L.append("The exact filter JSON (paste-ready) is in the accompanying `*-airk-filters.json`.")
    L.append("")
    return "\n".join(L)
