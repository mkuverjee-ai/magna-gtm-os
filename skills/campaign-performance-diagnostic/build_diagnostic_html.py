"""
Generic campaign performance diagnostic HTML builder.

Consumes the analysis JSON from analyze_leads.py plus a narrative
JSON and emits a self-contained HTML report.

Usage:
    python3 build_diagnostic_html.py \\
        --analysis _lead_analysis.json \\
        --narrative <company>_narrative.json \\
        --output <company>_Campaign_Performance_Diagnostic_<period>.html

Required narrative JSON fields:
    company_name          str   Display name of the company, eg "Acme"
    report_date           str   Display date, eg "May 2026"
    report_period         str   Eg "Performance Diagnostic, May 2026"
    eyebrow               str   Top-of-cover eyebrow, eg "Performance Diagnostic, May 2026"
    lede                  str   Short cover paragraph leading on positive replies story
    headline_callout      str   The single big callout under the KPI strip
    exec_finding_1        str   Paragraph 1 of "Three findings the data settled"
    exec_finding_2        str   Paragraph 2
    exec_finding_3        str   Paragraph 3
    exec_actions          list[str]  Three short action sentences for the exec summary
    action_plan           list[dict] Six items: {num, title, why, doing}
    future_inflight       list[dict] In-flight campaign cards: {title, pitch, footer}
    future_proposed       list[dict] Proposed campaign cards: {title, pitch, footer}
    case_study_industry   dict   case_study_company -> industry label
    custom_caveats        list[str]  Any additional callouts beyond the four standard ones

Palette is a neutral default (edit the tokens below to rebrand). Section structure is fixed. The four standard
caveats are always present:
  - Time window (2-3 month sliding window)
  - Persona / industry visibility (tagged before upload, not always pushed to Instantly)
  - Retired campaigns (low-volume rows in the campaign table)
  - Lead data source (industry data origin)
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

# Brand tokens
COLOR_PAGE = "#F6F7F9"
COLOR_INK = "#14171C"
COLOR_BLUE = "#2F6FEB"
COLOR_NAVY = "#1B3A7A"
COLOR_GREEN = "#6CCB9A"
COLOR_BORDER = "#DFE3EA"
COLOR_MUTED = "#5B6472"
COLOR_SURFACE = "#FFFFFF"
COLOR_SUCCESS = "#00C950"
COLOR_ERROR = "#FB2C36"
COLOR_WARN = "#FE9A00"


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--analysis", required=True, help="Path to _lead_analysis.json from analyze_leads.py")
    p.add_argument("--narrative", required=True, help="Path to <company>_narrative.json")
    p.add_argument("--output", required=True, help="Output HTML path")
    p.add_argument("--lemlist", help="Optional path to _lemlist_analysis.json for the LinkedIn pillar")
    return p.parse_args(argv)


def pct(x, decimals=2):
    return f"{x:.{decimals}f}%"


def num(x):
    return f"{x:,}"


def esc(s):
    return html.escape(str(s) if s is not None else "")


def rate_class(rate, threshold_good=2.0, threshold_ok=1.0):
    if rate >= threshold_good:
        return "rate-good"
    if rate >= threshold_ok:
        return "rate-ok"
    return "rate-bad"


def row_with_bar(rate, max_rate):
    width = (rate / max_rate * 100) if max_rate else 0
    return (
        f'<div class="bar-wrap">'
        f'<span style="font-variant-numeric:tabular-nums;font-weight:600;min-width:50px;text-align:right">{rate:.2f}%</span>'
        f'<div class="bar-track"><span class="bar-fill" style="width:{width:.1f}%"></span></div></div>'
    )


def build_css() -> str:
    return f"""
:root {{
  --page: {COLOR_PAGE}; --ink: {COLOR_INK}; --blue: {COLOR_BLUE}; --navy: {COLOR_NAVY};
  --green: {COLOR_GREEN}; --border: {COLOR_BORDER}; --muted: {COLOR_MUTED}; --surface: {COLOR_SURFACE};
  --success: {COLOR_SUCCESS}; --error: {COLOR_ERROR}; --warn: {COLOR_WARN};
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{
  background: var(--page); color: var(--ink);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
  font-size: 15px; line-height: 1.55;
  -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
}}
.page {{ max-width: 1180px; margin: 0 auto; padding: 56px 48px 80px; }}
h1, h2, h3, h4 {{
  font-family: 'Inter', -apple-system, sans-serif;
  font-weight: 700; letter-spacing: -0.01em; color: var(--ink); margin: 0 0 14px;
}}
h1 {{ font-size: 44px; line-height: 1.08; letter-spacing: -0.02em; }}
h2 {{ font-size: 26px; line-height: 1.2; margin-top: 56px; }}
h3 {{ font-size: 18px; line-height: 1.3; margin-top: 28px; color: var(--navy); }}
h4 {{ font-size: 15px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); margin-top: 0; margin-bottom: 8px; font-weight: 600; }}
p {{ margin: 0 0 14px; max-width: 78ch; }}
strong {{ color: var(--ink); font-weight: 600; }}
.cover {{ border-bottom: 1px solid var(--border); padding-bottom: 56px; margin-bottom: 16px; }}
.cover .eyebrow {{ font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--blue); margin-bottom: 18px; font-weight: 600; }}
.cover h1 {{ font-size: 56px; line-height: 1.04; }}
.cover .lede {{ font-size: 19px; color: var(--muted); max-width: 68ch; margin-top: 16px; }}
.cover-meta {{ margin-top: 32px; display: flex; gap: 40px; flex-wrap: wrap; font-size: 13px; color: var(--muted); }}
.cover-meta strong {{ display: block; color: var(--ink); font-size: 22px; font-family: 'Inter',sans-serif; }}
.kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 32px 0 8px; }}
.kpi {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 18px 18px 16px; }}
.kpi .label {{ font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); font-weight: 600; }}
.kpi .value {{ font-size: 28px; font-family: 'Inter',sans-serif; font-weight: 700; margin-top: 6px; color: var(--ink); }}
.kpi .sub {{ font-size: 12px; color: var(--muted); margin-top: 4px; }}
.callout {{ background: linear-gradient(180deg, rgba(47,111,235,0.04), rgba(47,111,235,0.0)); border-left: 3px solid var(--blue); padding: 14px 18px; margin: 16px 0; border-radius: 0 8px 8px 0; font-size: 14.5px; }}
.callout.green, .callout.lime {{ border-left-color: #2E9E68; background: linear-gradient(180deg, rgba(108,203,154,0.18), rgba(108,203,154,0.0)); }}
.callout.warn {{ border-left-color: var(--warn); background: linear-gradient(180deg, rgba(254,154,0,0.07), rgba(254,154,0,0.0)); }}
.callout.error {{ border-left-color: var(--error); background: linear-gradient(180deg, rgba(251,44,54,0.05), rgba(251,44,54,0.0)); }}
table {{ width: 100%; border-collapse: collapse; font-size: 13.5px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; margin: 12px 0 18px; }}
th, td {{ text-align: left; padding: 10px 14px; border-bottom: 1px solid var(--border); vertical-align: middle; }}
th {{ background: #EEF1F5; font-size: 11.5px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }}
tr:last-child td {{ border-bottom: none; }}
tbody tr:hover {{ background: rgba(47,111,235,0.025); }}
td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
td.center, th.center {{ text-align: center; }}
.bar-wrap {{ display: flex; align-items: center; gap: 10px; }}
.bar-track {{ flex: 1; height: 8px; background: rgba(47,111,235,0.08); border-radius: 4px; overflow: hidden; min-width: 60px; }}
.bar-fill {{ display: block; height: 100%; background: var(--blue); border-radius: 4px; }}
.rate-good {{ color: var(--navy); font-weight: 600; }}
.rate-ok {{ color: var(--ink); }}
.rate-bad {{ color: var(--error); font-weight: 600; }}
.pill {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; background: rgba(47,111,235,0.08); color: var(--navy); }}
.pill.new {{ background: rgba(108,203,154,0.35); color: #1D5C3E; }}
.pill.rt {{ background: rgba(47,111,235,0.10); color: var(--navy); }}
.trend {{ display: grid; grid-template-columns: 1fr; gap: 12px; margin: 18px 0 8px; }}
.trend-row {{ display: grid; grid-template-columns: 80px 1fr 160px; gap: 14px; align-items: center; font-size: 13px; }}
.trend-month {{ font-variant-numeric: tabular-nums; color: var(--muted); }}
.trend-bars {{ display: flex; flex-direction: column; gap: 4px; }}
.trend-bar {{ height: 14px; border-radius: 3px; background: var(--blue); display: flex; align-items: center; padding-left: 8px; color: white; font-size: 11px; font-weight: 600; font-variant-numeric: tabular-nums; min-width: 24px; white-space: nowrap; }}
.trend-bar.rt {{ background: #93B4F5; color: var(--navy); }}
.trend-bar.empty {{ background: rgba(47,111,235,0.10); color: var(--muted); }}
.trend-stats {{ text-align: right; color: var(--muted); font-size: 12px; }}
.legend {{ font-size: 12px; color: var(--muted); display: flex; gap: 18px; margin: 6px 0 0; flex-wrap: wrap; }}
.legend .sw {{ display: inline-block; width: 10px; height: 10px; border-radius: 2px; vertical-align: middle; margin-right: 6px; }}
.toc {{ font-size: 13px; color: var(--muted); margin: 18px 0 4px; }}
.toc a {{ color: var(--navy); margin-right: 14px; text-decoration: none; border-bottom: 1px dotted var(--border); }}
.toc a:hover {{ color: var(--blue); border-bottom-color: var(--blue); }}
.action {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 22px 26px; margin: 14px 0; display: grid; grid-template-columns: 36px 1fr; gap: 22px; align-items: start; }}
.action-num {{ font-family: 'Inter',sans-serif; font-weight: 700; font-size: 26px; color: var(--blue); line-height: 1; }}
.action h3 {{ margin-top: 0; color: var(--ink); }}
.action .why {{ font-size: 13.5px; color: var(--muted); margin: 8px 0; }}
.campaign-grid {{ display: grid; grid-template-columns: 1fr; gap: 14px; margin: 14px 0 26px; }}
.campaign-card {{ background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--blue); border-radius: 12px; padding: 22px 26px; }}
.campaign-card.inflight {{ border-left-color: #2E9E68; }}
.campaign-card .head {{ display: flex; align-items: center; gap: 12px; margin-bottom: 6px; }}
.campaign-card h3 {{ margin: 0; font-size: 17px; color: var(--ink); }}
.campaign-card .pill {{ font-size: 10.5px; letter-spacing: 0.08em; text-transform: uppercase; padding: 3px 10px; border-radius: 999px; background: rgba(47,111,235,0.10); color: var(--navy); font-weight: 700; }}
.campaign-card .pill.inflight {{ background: rgba(108,203,154,0.40); color: #1D5C3E; }}
.campaign-card .pitch {{ font-size: 14.5px; color: var(--ink); margin: 6px 0 12px; max-width: none; }}
.campaign-card .meta-line {{ font-size: 13px; color: var(--muted); margin: 4px 0 0; }}
.campaign-card .meta-line strong {{ color: var(--ink); }}
.campaign-group-label {{ font-size: 11.5px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); font-weight: 600; margin: 26px 0 8px; }}
footer {{ border-top: 1px solid var(--border); margin-top: 64px; padding-top: 24px; font-size: 12px; color: var(--muted); }}
"""


def rank_section(data_section, seg="new_outbound", min_c=200, exclude_keys=("unknown", "(no case study)", "")):
    rows = []
    for k, v in data_section.items():
        x = v[seg]
        if k in exclude_keys:
            continue
        if x["contacted"] >= min_c:
            rows.append((k, x))
    rows.sort(key=lambda r: -r[1]["reply_rate"])
    return rows


def render_segment_table(rows):
    if not rows:
        return '<tr><td colspan="6">Insufficient sample.</td></tr>'
    max_rate = max((r[1]["reply_rate"] for r in rows), default=1)
    out = []
    for k, x in rows:
        label = k.title() if isinstance(k, str) and k.islower() else k
        out.append(
            f'<tr>'
            f'<td>{esc(label)}</td>'
            f'<td class="num">{num(x["contacted"])}</td>'
            f'<td class="num">{num(x["replied"])}</td>'
            f'<td>{row_with_bar(x["reply_rate"], max_rate)}</td>'
            f'<td class="num"><span class="{rate_class(x["positive_rate"], 0.10, 0.03)}">{x["positive"]}</span></td>'
            f'<td class="num">{pct(x["bounce_rate"])}</td>'
            f"</tr>"
        )
    return "\n".join(out)


def render_case_study_table(rows, industry_map):
    if not rows:
        return '<tr><td colspan="7">Insufficient sample.</td></tr>'
    max_rate = max((r[1]["reply_rate"] for r in rows), default=1)
    out = []
    for k, x in rows:
        industry = industry_map.get(k, '<span style="color:#5B6472">(unmapped)</span>')
        out.append(
            f'<tr>'
            f'<td>{esc(k)}</td>'
            f'<td>{industry}</td>'
            f'<td class="num">{num(x["contacted"])}</td>'
            f'<td class="num">{num(x["replied"])}</td>'
            f'<td>{row_with_bar(x["reply_rate"], max_rate)}</td>'
            f'<td class="num"><span class="{rate_class(x["positive_rate"], 0.10, 0.03)}">{x["positive"]}</span></td>'
            f'<td class="num">{pct(x["bounce_rate"])}</td>'
            f"</tr>"
        )
    return "\n".join(out)


def render_simple_table(rows):
    if not rows:
        return '<tr><td colspan="4">Insufficient sample.</td></tr>'
    max_rate = max((r[1]["reply_rate"] for r in rows), default=1)
    out = []
    for k, x in rows:
        out.append(
            f'<tr>'
            f'<td>{esc(k)}</td>'
            f'<td class="num">{num(x["contacted"])}</td>'
            f'<td class="num">{num(x["replied"])}</td>'
            f'<td>{row_with_bar(x["reply_rate"], max_rate)}</td>'
            f"</tr>"
        )
    return "\n".join(out)


def render_copy_themes(fp_section, examples, seg="new_outbound", min_c=300, top_n=4, bottom_n=4):
    rows = [(fp, v[seg], examples.get(fp, fp)) for fp, v in fp_section.items() if v[seg]["contacted"] >= min_c]
    rows.sort(key=lambda r: -r[1]["reply_rate"])
    if not rows:
        return "<p>Insufficient sample for theme analysis.</p>"
    winners = rows[:top_n]
    losers = rows[-bottom_n:] if len(rows) > top_n else []
    parts = ['<h4>Themes that resonate</h4>']
    for fp, x, full in winners:
        parts.append(
            f'<div style="border-left:3px solid var(--success);padding:8px 14px;margin:8px 0;font-size:13.5px">'
            f'<div style="font-size:12px;color:var(--muted);margin-bottom:4px"><strong>{pct(x["reply_rate"])}</strong> reply rate '
            f'· n={num(x["contacted"])} · positive: {x["positive"]}</div>'
            f'<div style="font-style:italic">&ldquo;{esc(full)}&rdquo;</div></div>'
        )
    if losers:
        parts.append('<h4 style="margin-top:18px">Themes that are not landing</h4>')
        for fp, x, full in losers:
            parts.append(
                f'<div style="border-left:3px solid var(--error);padding:8px 14px;margin:8px 0;font-size:13.5px">'
                f'<div style="font-size:12px;color:var(--muted);margin-bottom:4px"><strong>{pct(x["reply_rate"])}</strong> reply rate '
                f'· n={num(x["contacted"])} · positive: {x["positive"]}</div>'
                f'<div style="font-style:italic">&ldquo;{esc(full)}&rdquo;</div></div>'
            )
    return "\n".join(parts)


def render_trend(data):
    recent = []
    for m in sorted(data["by_month"].keys()):
        if not m or m == "unknown":
            continue
        v = data["by_month"][m]
        if v["overall"]["contacted"] < 100:
            continue
        recent.append((m, v))
    recent = [(m, v) for m, v in recent if m >= sorted([r[0] for r in recent])[max(0, len(recent) - 12)]]
    if not recent:
        return "<p>Insufficient time-series data.</p>"
    max_rate = 1.0
    for m, v in recent:
        for seg in ("new_outbound", "retargeting"):
            if v[seg]["contacted"] >= 200:
                max_rate = max(max_rate, v[seg]["reply_rate"])
    rows = []
    for m, v in recent:
        new = v["new_outbound"]
        rt = v["retargeting"]

        def bar_html(seg, cls, label):
            if seg["contacted"] < 200:
                if seg["contacted"] == 0:
                    return f'<div class="trend-bar empty" style="width:0%">{label} no data</div>'
                w = seg["reply_rate"] / max_rate * 100
                return f'<div class="trend-bar empty" style="width:{w:.1f}%">{label} {seg["reply_rate"]:.2f}% (n={seg["contacted"]})</div>'
            w = seg["reply_rate"] / max_rate * 100
            return f'<div class="trend-bar {cls}" style="width:{w:.1f}%">{label} {seg["reply_rate"]:.2f}% (n={num(seg["contacted"])})</div>'

        nob = bar_html(new, "", "New")
        rtb = bar_html(rt, "rt", "Retarget") if rt["contacted"] > 0 else ""
        pos_rate = new["positive_rate"]
        pos_color = "#2E9E68" if pos_rate >= 0.10 else ("#14171C" if pos_rate >= 0.05 else "#FB2C36")
        pos_text = f'{new["positive"]} interested ({pos_rate:.3f}%)' if new["contacted"] >= 200 else "&nbsp;"
        rows.append(
            f'<div class="trend-row">'
            f'<div class="trend-month">{m}</div>'
            f'<div class="trend-bars">{nob}{rtb}</div>'
            f'<div class="trend-stats" style="color:{pos_color};font-weight:600">{pos_text}</div></div>'
        )
    return "\n".join(rows)


def render_action_plan(items):
    out = []
    for item in items:
        out.append(
            f'<div class="action">'
            f'<div class="action-num">{esc(item.get("num", ""))}</div>'
            f'<div>'
            f'<h3>{esc(item.get("title", ""))}</h3>'
            f'<p class="why">{item.get("why", "")}</p>'
            f'<p class="why"><strong>Doing this:</strong> {item.get("doing", "")}</p>'
            f"</div></div>"
        )
    return "\n".join(out)


def render_campaign_cards(items, pill_class="", pill_label="Proposed"):
    out = []
    for c in items:
        out.append(
            f'<div class="campaign-card {pill_class}">'
            f'<div class="head"><span class="pill {pill_class}">{esc(pill_label)}</span>'
            f'<h3>{esc(c.get("title", ""))}</h3></div>'
            f'<p class="pitch">{c.get("pitch", "")}</p>'
            f'<p class="meta-line">{c.get("footer", "")}</p>'
            f"</div>"
        )
    return "\n".join(out)


def build_html(analysis: dict, narrative: dict, lemlist: dict | None) -> str:
    overall = analysis["overall"]
    total_contacted = overall["overall"]["contacted"]
    total_replied = overall["overall"]["replied"]
    total_positive = overall["overall"]["positive"]
    total_bounced = overall["overall"]["bounced"]
    new_reply_rate = overall["new_outbound"]["reply_rate"]
    new_contacted = overall["new_outbound"]["contacted"]

    apr_new = (analysis.get("by_month", {}).get(narrative.get("kpi_month_a", ""), {}) or {}).get("new_outbound", {}) or {
        "positive_rate": 0,
        "positive": 0,
        "contacted": 0,
    }
    may_new = (analysis.get("by_month", {}).get(narrative.get("kpi_month_b", ""), {}) or {}).get("new_outbound", {}) or {
        "positive_rate": 0,
        "positive": 0,
        "contacted": 0,
    }

    persona_rows = rank_section(analysis.get("by_persona", {}), min_c=200)
    industry_rows = rank_section(analysis.get("by_industry", {}), min_c=200)
    case_rows = rank_section(analysis.get("by_case_study", {}), min_c=200)
    esp_rows = rank_section(analysis.get("by_email_provider", {}), min_c=200, exclude_keys=())
    esg_rows = rank_section(analysis.get("by_esg", {}), min_c=200, exclude_keys=())

    camp_rows = []
    for k, v in analysis.get("by_campaign", {}).items():
        o = v["overall"]
        if o["contacted"] >= 500:
            kind = "Retargeting" if "retarget" in k.lower() else "New Outbound"
            camp_rows.append((k, o, kind))
    camp_rows.sort(key=lambda r: -r[1]["reply_rate"])
    max_camp_rate = max((r[1]["reply_rate"] for r in camp_rows), default=1)
    camp_table_html = "\n".join(
        f'<tr>'
        f'<td>{esc(k)}</td>'
        f'<td class="center"><span class="pill {"rt" if kind=="Retargeting" else "new"}">{kind}</span></td>'
        f'<td class="num">{num(o["contacted"])}</td>'
        f'<td class="num">{num(o["replied"])}</td>'
        f'<td>{row_with_bar(o["reply_rate"], max_camp_rate)}</td>'
        f'<td class="num"><span class="{"rate-bad" if o["bounce_rate"]>=8 else ("rate-ok" if o["bounce_rate"]>=3 else "rate-good")}">{pct(o["bounce_rate"])}</span></td>'
        f'<td class="num">{o["positive"]}</td></tr>'
        for k, o, kind in camp_rows
    )

    company = narrative.get("company_name") or "Outbound"
    period = narrative["report_period"]
    eyebrow = narrative.get("eyebrow", period)
    lede = narrative.get("lede", "")
    headline_callout = narrative.get("headline_callout", "")
    custom_caveats_html = "\n".join(f'<div class="callout">{c}</div>' for c in narrative.get("custom_caveats", []))

    # Optional Lemlist pillar
    lemlist_section = ""
    if lemlist:
        ll = lemlist["overall"]
        lemlist_section = f"""
<section id="linkedin">
<h2>LinkedIn pillar (Lemlist)</h2>
<p>Headline LinkedIn performance from the Lemlist export. {esc(num(ll['uploaded']))} leads uploaded,
{esc(num(ll['engaged']))} engaged, {pct(ll['connection_rate'])} connection rate,
{pct(ll['reply_rate'])} reply rate, {ll['positive']} positive replies.</p>
</section>
"""

    css = build_css()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>{esc(company)} Campaign Performance Diagnostic, {esc(narrative.get('report_date',''))}</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>{css}</style>
</head>
<body>
<div class="page">

<section class="cover">
  <div class="eyebrow">{esc(eyebrow)}</div>
  <h1>{esc(company)} Campaign Diagnostic</h1>
  <p class="lede">{lede}</p>
  <p class="lede" style="font-size:14px;color:var(--muted);margin-top:10px">
    <strong>Scope of this analysis.</strong> The export covers the leads currently
    living inside Instantly. As campaigns rotate, older leads are deleted to make room
    for new ones, so this report effectively reflects the last two to three months of
    activity rather than the full programme history. Campaigns that appear with very
    low volume in the tables below are retired campaigns where most leads have already
    been removed.
  </p>
  <div class="cover-meta">
    <div><strong>{num(total_contacted)}</strong>leads contacted in window</div>
    <div><strong>{num(total_replied)}</strong>replies ({pct(overall['overall']['reply_rate'])})</div>
    <div><strong>{num(total_positive)}</strong>positive replies ({pct(total_positive/total_contacted*100,3) if total_contacted else '0%'})</div>
    <div><strong>{len(camp_rows)}</strong>campaigns in view</div>
  </div>
  <div class="toc">
    <a href="#summary">Executive summary</a>
    <a href="#trend">Performance over time</a>
    <a href="#campaigns">Campaign performance</a>
    <a href="#persona">Persona</a>
    <a href="#industry">Industry</a>
    <a href="#case">Case studies</a>
    <a href="#copy">Copy themes</a>
    <a href="#deliverability">Deliverability</a>
    <a href="#actions">Action plan</a>
    <a href="#campaigns-next">Future campaigns</a>
    <a href="#method">Methodology</a>
  </div>
</section>

<section id="summary">
<h2>Executive summary</h2>
<div class="kpi-row">
  <div class="kpi">
    <div class="label">Reference positive reply</div>
    <div class="value">{pct(apr_new.get('positive_rate',0),3)}</div>
    <div class="sub">{apr_new.get('positive',0)} interested on {num(apr_new.get('contacted',0))} contacted</div>
  </div>
  <div class="kpi">
    <div class="label">Current positive reply</div>
    <div class="value" style="color:var(--error)">{pct(may_new.get('positive_rate',0),3)}</div>
    <div class="sub">{may_new.get('positive',0)} interested on {num(may_new.get('contacted',0))} contacted</div>
  </div>
  <div class="kpi">
    <div class="label">New outbound reply rate</div>
    <div class="value">{pct(new_reply_rate)}</div>
    <div class="sub">{num(overall['new_outbound']['replied'])} replies on {num(new_contacted)} contacted</div>
  </div>
  <div class="kpi">
    <div class="label">Hard bounces</div>
    <div class="value">{pct(overall['overall']['bounce_rate'])}</div>
    <div class="sub">{num(total_bounced)} of {num(overall['overall']['uploaded'])} addresses uploaded</div>
  </div>
</div>

<div class="callout error">{headline_callout}</div>

<h3>Three findings the data settled</h3>
<p>{narrative.get('exec_finding_1','')}</p>
<p>{narrative.get('exec_finding_2','')}</p>
<p>{narrative.get('exec_finding_3','')}</p>

<h3>Three actions we are taking in the next two weeks</h3>
<ol>
{''.join(f'<li>{a}</li>' for a in narrative.get('exec_actions', []))}
</ol>

{custom_caveats_html}
</section>

<section id="trend">
<h2>Performance over time</h2>
<p>Monthly performance split by campaign type. The bars show reply rate. The colour-coded
text to the right of each row shows positive replies for new outbound, which is the metric
carrying the actual signal.</p>
<div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:24px 26px;margin:18px 0">
<div class="trend">
{render_trend(analysis)}
</div>
<div class="legend">
  <span><span class="sw" style="background:{COLOR_BLUE}"></span>New outbound (reply rate)</span>
  <span><span class="sw" style="background:#93B4F5"></span>Retargeting (reply rate)</span>
  <span><span class="sw" style="background:#2E9E68"></span>Healthy positive rate (&ge;0.10%)</span>
  <span><span class="sw" style="background:#FB2C36"></span>Positive replies under threshold</span>
</div>
</div>
</section>

<section id="campaigns">
<h2>Campaign-by-campaign performance</h2>
<p>All campaigns with at least 500 contacted leads currently visible in the export, ranked
by reply rate. Retargeting campaigns are marked separately.</p>
<div class="callout">
<strong>Reading note.</strong> Campaigns that look small or low-volume in this table are
retired campaigns where most of the contacts have already been deleted to make room for
new ones. The reply rate against the residual sample is still informative but the total
contacted is no longer a measure of how big that campaign was at the time.
</div>
<table>
  <thead><tr>
    <th>Campaign</th><th class="center">Type</th><th class="num">Contacted</th>
    <th class="num">Replied</th><th>Reply rate</th><th class="num">Bounce</th><th class="num">Positive</th>
  </tr></thead>
  <tbody>{camp_table_html}</tbody>
</table>
</section>

<section id="persona">
<h2>Persona diagnostic</h2>
<p>Leads are persona-tagged before copy is generated, but
the persona field is not always pushed into Instantly as a visible custom variable. The
view below is therefore based on the persona-tagged rows that we can see in the export
and is restricted to new-outbound contacts with at least 200 contacted leads.</p>
<table>
  <thead><tr><th>Persona</th><th class="num">Contacted</th><th class="num">Replied</th>
  <th>Reply rate</th><th class="num">Positive</th><th class="num">Bounce</th></tr></thead>
  <tbody>{render_segment_table(persona_rows)}</tbody>
</table>
</section>

<section id="industry">
<h2>Industry diagnostic</h2>
<p>Industry is not consistently pushed into Instantly as a custom variable at upload, so
this table reflects only the rows where industry data was carried through. The industry
data we do have originates from the lead data source used to build the lists. Cells with fewer
than 200 contacted are excluded. New outbound only.</p>
<table>
  <thead><tr><th>Industry</th><th class="num">Contacted</th><th class="num">Replied</th>
  <th>Reply rate</th><th class="num">Positive</th><th class="num">Bounce</th></tr></thead>
  <tbody>{render_segment_table(industry_rows)}</tbody>
</table>
</section>

<section id="case">
<h2>Case study performance</h2>
<p>The case-study sentence is the most variable part of the message and the strongest
predictor of reply rate. Below is every named case study with at least 200 contacted
leads on new outbound, sorted by reply rate.</p>
<table>
  <thead><tr>
    <th>Case study</th><th>Target industry</th><th class="num">Contacted</th><th class="num">Replied</th>
    <th>Reply rate</th><th class="num">Positive</th><th class="num">Bounce</th>
  </tr></thead>
  <tbody>{render_case_study_table(case_rows, narrative.get('case_study_industry', {}))}</tbody>
</table>
</section>

<section id="copy">
<h2>Copy themes</h2>
<h3>Value proposition paragraphs</h3>
<div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:24px 26px;margin:18px 0">
{render_copy_themes(analysis.get('by_vp_fp', {}), analysis.get('vp_examples', {}))}
</div>
<h3>Pain point paragraphs</h3>
<div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:24px 26px;margin:18px 0">
{render_copy_themes(analysis.get('by_pp_fp', {}), analysis.get('pp_examples', {}))}
</div>
</section>

<section id="deliverability">
<h2>Deliverability signals</h2>
<p>Reply rate is the only honest performance signal we use, since open and click tracking
are deliberately disabled across the programme to protect inbox placement.</p>
<h3>By email provider</h3>
<table><thead><tr><th>Provider</th><th class="num">Contacted</th><th class="num">Replied</th>
<th>Reply rate (new outbound)</th></tr></thead><tbody>{render_simple_table(esp_rows)}</tbody></table>
<h3>By email security gateway</h3>
<table><thead><tr><th>Gateway</th><th class="num">Contacted</th><th class="num">Replied</th>
<th>Reply rate (new outbound)</th></tr></thead><tbody>{render_simple_table(esg_rows)}</tbody></table>
</section>

{lemlist_section}

<section id="actions">
<h2>Action plan</h2>
<p>The changes we are making in the next two waves, ordered by expected
impact on positive-reply rate.</p>
{render_action_plan(narrative.get('action_plan', []))}
</section>

<section id="campaigns-next">
<h2>Next campaigns</h2>
<p>The action plan above is about getting more out of campaigns already running. This
section is about the new campaigns we want to launch next.</p>
<div class="campaign-group-label">In flight or already discussed</div>
<div class="campaign-grid">
{render_campaign_cards(narrative.get('future_inflight', []), pill_class='inflight', pill_label='In flight')}
</div>
<div class="campaign-group-label">New proposals</div>
<div class="campaign-grid">
{render_campaign_cards(narrative.get('future_proposed', []), pill_class='', pill_label='Proposed')}
</div>
</section>

<section id="method">
<h2>Methodology and definitions</h2>
<div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:24px 26px;margin:18px 0">
<h4>Source data</h4>
<p>Lead-level export from Instantly, {num(total_contacted)} leads contacted across {len(camp_rows)}
campaigns with at least 500 contacted leads. The export reflects the leads currently stored
in Instantly. As campaigns rotate, older leads are deleted to free capacity for new ones,
so this analysis is effectively a view of the last two to three months of activity, not the
full programme history.</p>
<h4>Reply rate</h4>
<p>Proportion of contacted leads where at least one reply was logged. Denominator excludes
uploaded leads never contacted.</p>
<h4>Positive reply</h4>
<p>Replies tagged "Interested" in the Instantly UI. Replies tagged "Not interested", "Wrong
person", or "Do not contact" are negative. Most replies sit in the default "Lead" state
and have not been manually classified yet.</p>
<h4>Open and click rate</h4>
<p>Intentionally disabled across the programme to protect inbox placement. Every metric
in this document is reply-based.</p>
<h4>Retargeting vs new outbound</h4>
<p>Any campaign whose name contains "{esc(analysis['meta']['retargeting_keyword'])}" is
classified as retargeting and shown separately throughout.</p>
<h4>Sample-size threshold</h4>
<p>Cells with fewer than 200 contacted leads (or 100 for deliverability splits) are
excluded to avoid reporting noise as signal.</p>
</div>
</section>

<footer>
{esc(company)} outbound programme &middot;
Diagnostic generated from Instantly export &middot;
{num(total_contacted)} contacted, {num(total_replied)} replies, {num(total_positive)} positive.
</footer>

</div>
</body>
</html>
"""


def main():
    args = parse_args()
    analysis = json.loads(Path(args.analysis).read_text())
    narrative = json.loads(Path(args.narrative).read_text())
    lemlist = json.loads(Path(args.lemlist).read_text()) if args.lemlist else None
    html_doc = build_html(analysis, narrative, lemlist)
    Path(args.output).write_text(html_doc, encoding="utf-8")
    print(f"Wrote {args.output} ({Path(args.output).stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
