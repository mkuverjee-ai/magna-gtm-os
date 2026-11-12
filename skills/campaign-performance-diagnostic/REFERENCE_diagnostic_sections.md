# Per-section content rules

Quick reference for what each section of the diagnostic should say and why. Use this together with `SKILL.md`.

The HTML builder (`build_diagnostic_html.py`) renders all of these sections automatically from the analysis JSON plus the narrative JSON config. Your job as the operator is to fill the narrative JSON correctly: the rules below tell you what to put in each field.

## Cover

- **Eyebrow:** "Performance Diagnostic, <month> <year>" or similar.
- **Title:** "<Company> Campaign Diagnostic".
- **Lede:** one paragraph that names the positive-reply story upfront. Example: "Reply volume held up in <recent month>, but positive replies dropped roughly Nx between <earlier month> and <recent month>. This document explains where the drop is coming from and the changes we are making to recover positive-reply rate."
- **Scope-of-analysis paragraph** is rendered automatically: always present.
- **KPI strip:** four cards: reference-month positive rate, current-month positive rate (coloured red if it dropped), new-outbound reply rate, bounce rate. Reference month is typically the most recent strong month; current month is the most recent month with data.
- **TOC anchors** are rendered automatically.

## Executive summary

- **Three findings.** Each finding is a self-contained short paragraph. The findings should be the three things that, taken together, explain the positive-reply slide. Order matters: most important finding first.
- **Three actions.** Three sentences, written for a busy reader to scan in ten seconds, each starting with an imperative verb ("Pivot...", "Rewrite...", "Split-route..."). The detailed action plan lives further down; these three are the headline.
- **Custom caveats.** Anything beyond the four standard caveats goes here as `custom_caveats` in the narrative JSON. Examples: a recent one-off campaign that produced anomalous data, a purchased-list data-source caveat, a recent restart/cleanup that changes how the numbers should be read.

## Performance over time

Rendered automatically from the analysis JSON. Each row of the chart shows:
- Month label
- New-outbound bar (blue) with reply rate and contacted count
- Retargeting bar (lighter blue) if any retargeting volume that month
- Positive replies for new outbound, colour-coded:
  - Green if ≥ 0.10% (healthy)
  - Ink if 0.05-0.10% (acceptable)
  - Red if < 0.05% (under threshold)

The chart is the most important visual in the report. It is where the positive-reply slide reads at a glance. Make sure the time window includes at least one strong reference month for contrast.

## Campaign-by-campaign performance

Rendered automatically. The "Reading note" callout is rendered automatically: it explains why low-volume campaigns are retired, not weak. Do NOT add narrative around individual campaigns inside this section; the action plan and future-campaigns sections are where campaign-level commentary lives.

## Persona diagnostic

- Table rendered automatically.
- The persona-visibility caveat sentence is rendered automatically.
- Optional callouts to add via custom_caveats:
  - "Personas we are adding for the next wave" (green callout): lists new persona buckets the team decided to add.
  - "Personas we are filtering out for the next wave" (warn callout): lists removed buckets.
- If the play briefs, learnings or call notes record specific persona changes, they belong here.

## Industry diagnostic

- Table rendered automatically.
- The lead-data-source caveat is rendered automatically.
- Use a callout to flag any "pulling the average down" sectors if there is a story to tell. If the underperformance has a process explanation (eg one purchased-list wave shipped without case studies), reframe accordingly. Never recommend "commission new case studies" without checking that none exist.

## Case study performance

- Table rendered automatically. Each case study gets a Target industry column populated from `case_study_industry` in the narrative JSON.
- **You must supply the case_study_industry mapping**: the script renders "(unmapped)" otherwise. Map each company to its sector from `company/context.md` (proof section) or the case study itself on your website.
- Trailing bullets to add via custom_caveats: roll the strongest case studies wider; reshuffle existing case studies for underperforming sectors; ask marketing for newer / more impressive material.

## Copy themes

- Rendered automatically from the analysis JSON fingerprints.
- The contrast between sector-anchored copy and generic copy will show up if the data has it. If the contrast is weak, that itself is a finding worth surfacing in custom_caveats.

## Deliverability signals

- ESP and ESG tables rendered automatically.
- The Microsoft + Mimecast / Proofpoint penalty is a well-known pattern. If the data shows it, surface the split-lane recommendation in the action plan.

## Action plan

`action_plan` in the narrative JSON. Six items recommended, each with:
- `num`: display number 1-6.
- `title`: short imperative-style title.
- `why`: one short paragraph explaining the reason (anchor in data + the play context).
- `doing`: one short paragraph explaining the specific operational step the team is taking.

Order by expected positive-reply lift. The first item should be the highest-impact change.

Standard recurring action items to consider (use only if they match the data):
1. Sector pivot to responsive sectors.
2. Rewrite value-prop and pain-point paragraphs with explicit industry names.
3. Microsoft + gateway split-lane setup.
4. Expand the use of winning case studies.
5. Reshuffle existing case studies into underperforming sectors. **Never** "commission new case studies" without checking that none exist.
6. List-source hygiene: lead sources that were already dropped stay dropped (frame as "keep them retired").

## Next campaigns

Two sub-sections, both rendered as cards from the narrative JSON:
- `future_inflight`: campaigns the team has already agreed to. Green "In flight" pill. Each card: `title`, `pitch` (one-line pitch in larger type), `footer` (Why now / What we need).
- `future_proposed`: new proposals. Blue "Proposed" pill.

The cards should reflect what the team has actually decided. If an idea has not yet been agreed, it goes in `future_proposed`. If it has, it goes in `future_inflight`.

Common in-flight campaign types: targeted lists built from your own customer data, champion tracking, current-customer expansion.

Common proposed campaign types: lookalikes of positive repliers, a public-record trigger (filings, permits, regulation dates), a lead-magnet offer from `/pvp-builder`, a new vertical, a new buyer persona.

## Methodology

Rendered automatically. Lists reply-rate denominator, retargeting classification, sample-size threshold, positive-reply definition, and the open-and-click-tracking-off note. No per-report tuning needed.

---

## Narrative JSON template

```json
{
  "company_name": "Acme",
  "report_date": "May 2026",
  "report_period": "Performance Diagnostic, May 2026",
  "eyebrow": "Performance Diagnostic, May 2026",
  "kpi_month_a": "2026-04",
  "kpi_month_b": "2026-05",
  "lede": "...",
  "headline_callout": "<strong>The headline.</strong> ...",
  "exec_finding_1": "<strong>1. ...</strong> ...",
  "exec_finding_2": "<strong>2. ...</strong> ...",
  "exec_finding_3": "<strong>3. ...</strong> ...",
  "exec_actions": [
    "<strong>Reshape the next two campaign waves...</strong>...",
    "<strong>Rewrite every generic value-proposition...</strong>...",
    "<strong>Split-route Microsoft-hosted...</strong>..."
  ],
  "action_plan": [
    {"num": "1", "title": "...", "why": "...", "doing": "..."},
    {"num": "2", "title": "...", "why": "...", "doing": "..."}
  ],
  "future_inflight": [
    {"title": "Customer lookalike campaign", "pitch": "...", "footer": "<strong>Why now:</strong> ..."}
  ],
  "future_proposed": [
    {"title": "Lookalike from positive replies", "pitch": "...", "footer": "<strong>Why now:</strong> ..."}
  ],
  "case_study_industry": {
    "Example Hotel Group": "Hotels & hospitality groups",
    "Example Manufacturing Co": "Electronics manufacturing"
  },
  "custom_caveats": [
    "<strong>Optional callout:</strong> any extra context that does not fit elsewhere."
  ]
}
```

Save this as `<company>_narrative.json` next to the analysis JSON, then pass both to `build_diagnostic_html.py`.
