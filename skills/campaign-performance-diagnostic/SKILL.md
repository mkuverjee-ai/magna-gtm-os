---
name: campaign-performance-diagnostic
description: Build a self-contained HTML campaign-performance diagnostic from a fresh Instantly (and optional Lemlist) lead export. Splits retargeting vs new outbound, surfaces positive replies as the headline metric, and lands on a concrete action plan and a Next Campaigns section. Trigger when someone asks for a "campaign diagnostic", "retrospective", "performance report", "why are replies dropping", or any outbound retrospective tied to an Instantly / Lemlist export, for one play or the whole programme.
---

# Campaign Performance Diagnostic

Builds a leadership-ready HTML diagnostic of your own outbound programme: cover with
positive-reply rate as the headline KPI, executive summary, time-trend chart split by retargeting
vs new outbound, persona / industry / case-study / copy-theme / deliverability cuts, an action
plan, and a Next Campaigns section.

The skill bundles two analysis scripts (Instantly + optional Lemlist) and one HTML builder. You
bring the context (company context, ICP, play briefs, past learnings, call notes if you record
calls) so the narrative reflects what the team actually decided, not just the numbers.

## Inputs to collect BEFORE you start

The skill refuses to ship a draft until items 1, 5 and 6 are in hand. The rest are conditional.

| # | Input | Required? | Why we need it |
|---|-------|-----------|----------------|
| 1 | **Instantly lead export CSV** | Mandatory | The primary data. Leads, replies, statuses, ESP, ESG, custom variables. |
| 2 | Lemlist lead export CSV | If LinkedIn is in scope | LinkedIn-channel data. The diagnostic adds a LinkedIn pillar if present. |
| 3 | Instantly API access | Optional | Fresh pulls, single-lead lookups, missing-field repair (read-only). |
| 4 | Lemlist API access | Optional | Same, for the LinkedIn pillar (read-only). |
| 5 | **Company context** | Mandatory | `company/context.md` (`python3 gtm.py company`): positioning, proof, personas, offers, sender domains. |
| 6 | **ICP matrix** | Mandatory | Persona x industry x company-size target spec. Lets the diagnostic compare contacted volume against the spec. |
| 7 | Play briefs and learnings | Strongly recommended | `plays/<play-slug>/campaigns/campaign-brief.md`, `reports/campaign-learnings.md`, and `python3 gtm.py intel`: what each campaign was meant to do and what is already retired. |
| 8 | Recent internal or sales-call notes | Optional | `python3 gtm.py meetings` / `gtm.py transcript --date ...` if you record calls: decisions, pivots, what leadership already pushed back on. |
| 9 | Company website | Fallback | When the above leaves a gap on positioning, sector framing, or case studies. |

If a mandatory input is missing, ask for it before starting. Do not fabricate.

## How to run

The pipeline has three stages: analysis, narrative drafting, HTML build. Save everything in the
play's `reports/` folder (`plays/<play-slug>/reports/`), or a programme-wide `reports/` folder
when the diagnostic covers several plays.

### Stage 1: Run the analysis script

```bash
python3 skills/campaign-performance-diagnostic/analyze_leads.py "<path to instantly export.csv>"
```

Optional flags:
- `--retargeting-keyword <word>`: substring used to classify a campaign as retargeting (default: `retarget`).
- `--min-sample <N>`: minimum contacted count before a cell is reported as confident (default: 200).
- `--output <path>`: override JSON output path (default: `_lead_analysis.json` next to the input).

If a Lemlist export is provided:
```bash
python3 skills/campaign-performance-diagnostic/analyze_lemlist.py "<path to lemlist export.csv>"
```

The JSON output contains overall stats, by-month breakdowns, by-campaign, by-persona, by-industry,
by-persona-industry, by-size, by-case-study, by-email-provider, by-email-security-gateway, and
copy-theme fingerprints. All cuts are split into retargeting vs new outbound vs overall.

### Stage 2: Draft the narrative

Before invoking the HTML builder, read:
- the analysis JSON (the numbers)
- `company/context.md` and the ICP matrix (the target spec to compare against)
- the play briefs and learnings, and `gtm.py intel` (what was intended, what is retired)
- recent call notes, if you have them (decisions, pivots, who matters)

Then prepare a narrative JSON config containing:
- `company_name`, `report_date`, `report_period`
- `exec_finding_1..3`: the three lead findings, in plain language, drawn from the numbers + context
- `action_plan`: six concrete actions ordered by expected positive-reply lift
- `future_inflight`: campaigns already agreed / launching
- `future_proposed`: new campaigns you want to put on the table
- `case_study_industry`: case-study company -> target industry mapping
- `custom_caveats`: anything beyond the four standard caveats (eg a purchased lead source, a one-off wave)

Save the config as `<company>_narrative.json` next to the analysis JSON.
`REFERENCE_diagnostic_sections.md` has the full template and what goes in each field.

### Stage 3: Build the HTML

```bash
python3 skills/campaign-performance-diagnostic/build_diagnostic_html.py \
    --analysis "<path to _lead_analysis.json>" \
    --narrative "<path to <company>_narrative.json>" \
    --output "<company>_Campaign_Performance_Diagnostic_<period>.html"
```

The script bakes in:
- A neutral palette (light grey page, blue accents, green second series, near-black ink, grey borders).
  Swap the colour tokens at the top of `build_diagnostic_html.py` for your own brand if you want.
- All four standard caveats (time window, persona / industry visibility, retired campaigns, lead data source).
- The Next Campaigns section scaffold with in-flight + proposed card styles.
- The methodology appendix.

## Editorial rules (do not skip these)

Each rule is a mistake that has been made before. Treat this list as load-bearing.

1. **Headline metric is positive-reply rate, never blended reply rate.** Reply rate can rise while positives collapse. Show both, but the cover KPI and the executive-summary headline callout both lead with positives.
2. **Retargeting vs new outbound is split everywhere.** Retargeting reads warmed leads and inflates the blended number. Time trend, segment cuts, and KPI cards all show the split. Anything cross-comparing the two is wrong.
3. **If open and click tracking are off (recommended for deliverability), never cite open or click rate**, even if the export has columns for them. The data is zero by design.
4. **Instantly exports are often a 2-3 month sliding window.** Older leads get deleted as new campaigns rotate in. State this on the cover and in the methodology. Campaigns with very low contacted counts in the table are usually retired campaigns where most leads have been removed, not poor performers.
5. **Missing persona / industry / company-size data in the export is a visibility gap, not list hygiene.** Personas tagged before upload are not always pushed into Instantly as custom variables. Industry data, where present, usually came from the lead data source (AI Ark or whatever list you bought) and should be attributed as such. Don't recommend "tighten persona tagging" unless you have checked the source lists.
6. **Never recommend commissioning new case studies** without first checking with marketing that none exist. The default reframe is "reshuffle existing case studies, and ask for any newer or more impressive material".
7. **Lead sources that underperformed and were already dropped are framed as already-retired**, not as new actions. Check the play learnings and `gtm.py intel` first.
8. **Sector-anchored copy usually outperforms generic copy by a wide margin (roughly 3-5x has been measured).** When a segment underperforms, check the copy-personalisation explanation before concluding the audience is wrong. The copy-theme fingerprints in the analysis JSON make this easy to surface.
9. **Microsoft + Mimecast / Proofpoint / Barracuda is a real performance penalty.** When the deliverability split shows it, recommend the split-lane setup (dedicated mailboxes, slower cadence, lighter HTML).
10. **Read the context before writing the narrative.** Persona requests, sector pivots, retired campaigns and team decisions live in the play briefs, learnings and call notes, and need to be reflected in the action plan and Next Campaigns section. Skipping them produces a diagnostic that feels disconnected from what the team is actually doing.

## Required sections in the HTML report

Section order is load-bearing. Do not skip or reorder.

1. **Cover**: title, eyebrow, lede with the positive-reply headline, time-window caveat, KPI strip (reference-month positive rate, current-month positive rate, new-outbound reply rate, bounce rate), TOC anchors.
2. **Executive summary**: three findings + three action items, surfaced before any chart. Lead with the positive-replies-vs-reply-rate story.
3. **Performance over time**: month-by-month bars, retargeting vs new outbound on the same chart, with positive-reply count + rate annotated on each month and colour-coded against a 0.10% / 0.05% threshold.
4. **Campaign-by-campaign performance**: table, retargeting marked separately, retired-campaigns caveat callout above.
5. **Persona diagnostic**: table of personas from the export. Persona-visibility caveat sentence at the top. Optional callouts: "personas we are adding for the next wave" and "personas we are filtering out".
6. **Industry diagnostic**: table. Lead-data-source caveat at the top.
7. **Case-study performance**: table with **Target industry** column mapping each case-study company to its sector. Trailing bullets: roll the strongest case studies wider; reshuffle existing case studies for underperforming sectors; ask for any newer material.
8. **Copy themes**: value-prop and pain-point fingerprints split into winners and losers, with the actual text quoted.
9. **Deliverability signals**: ESP and ESG splits, Microsoft + gateway callout, split-lane recommendation.
10. **Action plan**: six concrete actions, numbered, ordered by expected positive-reply lift.
11. **Next campaigns**: in-flight cards (green pill, "In flight") and proposed cards (blue pill, "Proposed"), each with a one-line pitch and a "Why now" / "What we need" footer.
12. **Methodology and definitions**: reply-rate denominator, retargeting classification, open / click tracking note, time-window note, sample-size threshold, fingerprint-grouping rule.

## Verification checklist

Before sharing, run through:

- [ ] Zero em dashes anywhere in the HTML.
- [ ] Cover KPI strip leads with positive-reply rate, not blended reply rate.
- [ ] Time trend chart shows positive-reply counts per month and colour-codes them.
- [ ] All four standard caveats present: time window (cover + methodology), persona / industry visibility (persona + industry sections), retired campaigns (campaign table), lead data source (industry section).
- [ ] No open-rate or click-rate citations anywhere (if tracking is off).
- [ ] Retargeting vs new outbound split shown in the time trend AND in every segment cut.
- [ ] Case-study table has a Target industry column.
- [ ] Action plan items reference specific decisions from the play briefs, learnings or call notes. Generic action plans are a smell that the context was not read.
- [ ] Next Campaigns section names in-flight vs proposed campaigns and what each one needs.
- [ ] Action plan does not recommend commissioning new case studies unless you confirmed none exist.
- [ ] No internal jargon if the report goes beyond the outbound team (no "spintax", no campaign IDs, no tooling references).
- [ ] HTML is self-contained: no external CDNs, no Javascript, opens without internet.

Then log the top findings so the next play starts from them:
`python3 gtm.py log-intel --play <play-slug> --category performance --label "..." --insight "..."`.

## Customisation

The bundled scripts avoid hardcoding any company name, sector, or case study. Per-report
adjustments happen in two places only:

1. **The narrative JSON config** (Stage 2): company_name, period, findings, action items, next campaigns, case study -> industry map, custom caveats.
2. **The context reading** (Stage 2): informs the narrative JSON.

Section structure and the 10 editorial rules do not change between reports.

## Reference

- Per-section content rules and the narrative JSON template: `REFERENCE_diagnostic_sections.md` in this folder.
- Sibling skills: `list-dedup` (list prep upstream), `email-metrics-benchmarks` (what "good" looks like), `lemlist-reporting`.
