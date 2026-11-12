---
name: icp-tam-mapper
description: Turn a domain or segment into an ICP Matrix plus a live AI Ark TAM/SAM/SOM breakdown. Use when scoping a new play or sizing a market before campaign work.
---

> **This skill only COUNTS.** `airk.py` runs size-1 searches and reads `totalElements`, so there are
> no records to give back. The moment you actually pull the list, use
> `python3 skills/ai-ark/aiark.py` and save the CSV under the play's `leads/` folder.

# ICP → TAM Mapper — Skill Reference

## What This Is

An end-to-end skill: **give it a domain, get back an ICP Matrix (XLSX) + a live AI Ark
TAM → SAM → SOM breakdown.** It replicates, in one repeatable pipeline, the manual work of
researching a company, building a 5-sheet ICP matrix, translating that ICP into AI Ark search
filters, and running live market-size + persona counts.

```
domain ──► research (Claude) ──► icp.json ──► build.py ──► ┌ {Company}_ICP_Matrix.xlsx  (+ CSVs)
                                                            ├ {company}-airk-filters.json (paste-ready)
                                                            └ {Company}_TAM_Breakdown.md  (live counts)
```

All filter logic is baked in. The AI Ark key comes from `gtm.cred("AI_ARK_API_KEY")` (add it with
`python3 gtm.py set-key AI_ARK_API_KEY`); nothing is hard-coded.

---

## When to Use

- "Do the ICP + TAM thing for {domain}"
- "Build an ICP matrix and size the market for {company}"
- "What filters do I put into AI Ark for this ICP?" (feed it an existing ICP → get filters + counts)
- Starting a new play: matrix + market size before campaign work
- Prospect qualification: is the addressable market big enough to be worth it?

---

## Output (what the user gets)

| File | What it is |
|------|-----------|
| `{Company}_ICP_Matrix.xlsx` | The 5-sheet ICP matrix (Account / Prospect / Persona / Signal Scoring / Case Study). Calibri, dark-blue headers. |
| `{Company}_ICP_Matrix_*.csv` | One CSV per sheet (for Sheets / Clay import). |
| `{company}-airk-filters.json` | The exact AI Ark filter JSON — company (TAM/SAM/SOM) + persona contact filters. Paste-ready into AI Ark or `skills/ai-ark/aiark.py --body`. |
| `{Company}_TAM_Breakdown.md` | The market funnel with **live counts**: TAM → SAM → SOM, buyers-within-SAM per persona, and a "what AI Ark can't filter → layer in Clay" section. |

---

## How To Run It (the flow Claude follows)

### Step 1 — Research the domain
Use `WebFetch` / `WebSearch` (and `company/context.md` when the domain is your own) to learn:
- What the product does (one sentence) and **who buys it** (this is the ICP — often *not* the obvious industry)
- Company size band, geographies, pricing/fee model, competitors, tech/CRM stack
- The **Key Qualifying Signal** — the one metric that separates good fits from bad
- Named customers, dream clients, and who to explicitly exclude

> ⚠️ The ICP is *who they should sell to*, not what they are. E.g. a company that builds an AI
> recruiting autopilot → the ICP is **executive search firms**, not "AI companies."

### Step 2 — Author `icp.json`
Write an `icp.json` conforming to `icp_schema.json`. Two blocks:

- **`matrix`** — the rich prose ICP (drives the XLSX). Same format/quality bar as
  `skills/icp-matrix`: 8 account rows, 4 prospect rows, 5-6 personas (challenges ↔ benefits mirror
  1:1), a 100-point scoring model (max_points sum to exactly 100), and case-study reference.
  Every cell is specific with `SOURCE:` citations — never thin one-liners.
- **`airk`** — the filter spec (drives the funnel): `icp_type`, geographies, industries, keyword
  gate, employee band, sweet spot, revenue floor, and buyer personas (titles + seniorities + dept).

Start from `icp_schema.json`. Once you have one finished `icp.json` you trust, keep it (e.g. in
`plays/<play-slug>/research/icp.json`) and copy it as the template for the next one.

#### Choosing `icp_type` (the most important AI Ark decision)
| Type | Use when | Funnel gate |
|------|----------|-------------|
| `firmographic` | A clean LinkedIn industry defines the ICP (e.g. "Banks, 500+ emp") | industries only |
| `signal_defined` | No clean industry — defined by what they *do/use/build* (e.g. "runs GPU workloads") | keyword only |
| `hybrid` | A sub-segment inside a broad industry (e.g. **executive search** inside *Staffing & Recruiting*) | industry **+** keyword gate |

Most B2B ICPs that look firmographic are actually **hybrid** — the industry is too broad and needs a
keyword gate to isolate the real target. When in doubt, use `hybrid`.

### Step 3 — Run the pipeline
```bash
python3 skills/icp-tam-mapper/build.py plays/<play-slug>/research/icp.json [output_dir]
```
This builds the XLSX + CSVs, writes the AI Ark filter JSON, runs **live** counts, and writes the
breakdown markdown. Output goes next to the icp.json unless you pass an output dir.

### Step 4 — Deliver
Open the XLSX for the user and paste the breakdown (TAM/SAM/SOM + personas + Clay signals). Offer
next steps: widen SAM (more geos/keywords), or export the SOM + economic-buyer slice with emails.

---

## The Funnel Logic (what build.py does)

| Segment | Geo | Size | Gate |
|---------|-----|------|------|
| **TAM** | all `geographies` | full `employee_min`–`employee_max` | broad `industries` (or none) — the widest defensible market |
| **SAM** | `priority_geographies` | full band | the core "what they are" gate: industries + keyword (hybrid), keyword (signal), or industries (firmographic) + exclusions |
| **SOM** | priority geos | `sweet_spot` band | same gate as SAM + optional `revenue_floor` |

Personas are counted **within the SAM company base** (so a persona count = "economic buyers at SAM-qualified firms"). Personas overlap — never sum them.

---

## AI Ark Filter Cheatsheet (gotchas baked into airk.py)

- Company filter key is **`account`**, people filter key is **`contact`** (not `accountFilter`/`contactFilter` — those are silently ignored on the raw API).
- `employeeSize` needs `{"type":"RANGE","range":[{"start","end"}]}` — key is `range`, not `ranges`.
- `industries` include is `{"mode":"SMART","content":[...]}`, not a bare array.
- `keyword.exclude` must use the **same `{sources, content}` shape** as `include` — a bare array returns `400 request not readable`. (airk.py handles this.)
- Seniorities are **lowercase** enums: `founder owner partner c_suite vp director head manager senior mid-level entry intern`.
- Title filter lives under `contact.experience.current.title`. Never put bare "Founder" in titles (it's a seniority; it over-matches).
- The AI Ark edge WAF **403s the default Python-urllib UA** — airk.py sends a browser UA.
- Old system-Python TLS gets rejected by AI Ark; airk.py **falls back to `curl`** automatically.
- Location filter is restrictive — for a real *export* (not just counts), search broad and post-filter locally.
- All calls here are **size:1 count-only** and **read-only** (search endpoints). Never write.

Full API reference: `skills/ai-ark/SKILL.md` and `skills/ai-ark/reference.md`.

---

## Files

```
icp-tam-mapper/
├── SKILL.md              # this file
├── build.py             # orchestrator: icp.json → XLSX + filters + breakdown
├── icp_matrix.py        # ICP matrix → styled 5-sheet XLSX (+ CSVs)
├── airk.py              # AI Ark: filters + live counts + breakdown markdown (read-only)
├── config.py            # key lookup (env → gtm.cred), region/industry expansion maps, keyword sources
├── generate_icp.py      # OPTIONAL headless ICP authoring (Claude API) from research notes
├── icp_schema.json      # the icp.json contract
├── requirements.txt     # openpyxl (+ anthropic for generate_icp.py)
└── .env.example
```

---

## Optional: headless ICP authoring

If you want to skip in-session research, `generate_icp.py` calls Claude to draft the `icp.json`
from research notes:
```bash
python3 generate_icp.py --domain acme.com --research notes.txt [--example good_icp.json] --out icp.json
python3 build.py icp.json
```
Needs `ANTHROPIC_API_KEY`. In-session authoring by Claude (Step 2) is higher quality — prefer it.

---

## Worked Example — AI recruiting autopilot (illustrative)

- **Product:** an AI talent-acquisition autopilot ("brief in → shortlist out").
- **ICP:** retained **executive search firms** — `hybrid` (Staffing & Recruiting + "executive search" keyword gate, minus contingency/temp/RPO).
- **Live funnel (one real run):** TAM 64,860 → SAM 7,476 (~11.5%) → SOM 1,788.
- **Buyers in SAM:** economic buyers 3,249 · heads of research 372 · consultants 2,687 · COO/ops 271.
- **Clay layer:** retained-vs-contingency fee model, mandate volume, researcher headcount, search-CRM detection, partner AI-in-search activity.

The lesson: the industry alone (Staffing & Recruiting) would have returned ~9x the real market. The keyword gate is what made SAM honest.
