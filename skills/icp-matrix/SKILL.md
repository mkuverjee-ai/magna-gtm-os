---
name: icp-matrix
description: "Build a complete 5-sheet ICP Matrix (Account Level, Prospect Level, Persona Matrix, Signal Scoring, Case Study Reference) from the company domain and company/context.md. Outputs styled .xlsx + per-sheet .csv files."
---

# ICP Matrix Builder Skill

## When to Use

- First setup of the OS — need a full ICP definition before building target lists or campaigns
- Starting a new play that targets a segment the existing matrix does not cover
- Need a structured, research-backed ICP matrix to drive lead sourcing, scoring, and outreach
- Refreshing or rebuilding the ICP after market/product changes

## Required Inputs

| Input | Required | Description |
|-------|----------|-------------|
| **Company domain** | Yes | your own domain, e.g. `acme.com` |
| **`company/context.md`** | Yes | ICP, positioning, proof, personas, exclusions. The source of truth. |
| **Sales call notes / win-loss** | Recommended | Recent call summaries, won/lost deal notes |
| **Firecrawl API key** | Optional | For deep website scraping beyond basic fetch, if you have a key |

## Output

A single `.xlsx` workbook with 5 sheets + 5 individual `.csv` files. Company-wide matrix goes in
`company/`; a segment-specific matrix goes in `plays/<play-slug>/research/`:

```
plays/<play-slug>/research/          (or company/ for the company-wide matrix)
├── {Company}_ICP_Matrix.xlsx          # Full workbook (5 sheets, styled)
├── {Company}_ICP_Matrix_Account_Level.csv
├── {Company}_ICP_Matrix_Prospect_Level.csv
├── {Company}_ICP_Matrix_Persona_Matrix.csv
├── {Company}_ICP_Matrix_Signal_Scoring.csv
└── {Company}_ICP_Matrix_Case_Study_Reference.csv
```

---

## Framework

### Phase 1 — Extract Company Context (Source of Truth)

`company/context.md` is the **single source of truth**. Every field maps directly to ICP matrix cells. When web research conflicts with it, the context file wins unless it is clearly outdated or incomplete (then update it).

Read it and extract ALL of the following. If a field is missing, flag it for web research.

**Company Identity:**
- Company name, domain, one-line summary
- Core problem they solve (in customer's words)
- Unique solution / differentiator
- Pricing tiers and ACV ranges

**Target Market (maps to Account Level sheet):**
- Target countries / geography
- Target industries / verticals (+ any excluded industries)
- Employee count range (min/max)
- Revenue range (may have multiple tiers)
- Business model / structure (the KEY qualifying criteria — e.g., "PE-backed", "multi-location", "$500K+/mo ad spend")
- Funding / ownership signals
- Tech stack signals (what prospects currently use)
- Target domains (dream clients) and excluded domains (with exclusion rationale)

**Target Personas (maps to Prospect Level + Persona Matrix sheets):**
- Target titles / seniority levels
- Target departments / job functions
- How the buyer varies by company size
- LinkedIn profile keywords
- LinkedIn activity signals

**Sales Context (maps to Signal Scoring + Case Study sheets):**
- Sales trigger tiers (Tier 1, 2, 3)
- Competitors / displacement targets
- ICP segments (the distinct buyer archetypes)
- Max target companies
- Exclusions and disqualification criteria

**Call notes / win-loss (if available):**
- Revenue range refinements
- ACV targets
- Segment priorities
- Competitive positioning
- Any corrections or additions to the context file

### Phase 2 — Deep Company Research

After extracting the context, research the company to fill gaps, validate claims, and gather case study evidence.

**Website research (fetch the domain + key pages):**
- Homepage: positioning, tagline, social proof (logos, stats)
- Pricing page: tier names, pricing model, target segments
- Customers/case studies page: named clients, industry spread, use cases
- About page: founding story, team size, funding, mission
- Product pages: features that map to persona pain points
- Integration/partner pages: tech stack compatibility

**Web search queries (run 3-5 targeted searches):**
1. `"{company name}" funding OR Series OR raised` — funding history
2. `"{company name}" competitors OR alternative OR vs` — competitive landscape
3. `"{company name}" reviews OR customers OR case study` — social proof
4. `"{company name}" revenue OR ARR OR valuation` — market position
5. `site:linkedin.com/company/{company}` — company LinkedIn data

**Data to collect:**
- Total funding raised, latest round, key investors
- Revenue estimate (if public or reported)
- Employee count / headcount trends
- Named customers (with industry tags)
- Competitor list (direct + indirect)
- Key integrations and tech partnerships
- Geographic presence
- Recent news (M&A, product launches, executive hires)

### Phase 3 — Build Sheet 1: Account Level

**Format:** 3-column table — `Lead Score Category` | `Qualified` | `Prioritization`

**Required rows (8 dimensions):**

| Row | Description | How to Fill |
|-----|-------------|-------------|
| **LOCATION / GEOGRAPHY** | Target countries from context | Prioritize by market focus. Note if other markets handled by other teams. |
| **EMPLOYEE COUNT** | Min-max from context | Create 3-4 tiers. Note when employee count is a weak signal (explain why). |
| **INDUSTRY / VERTICAL** | Industries from context + research | Tier 1 (highest priority), Tier 2 (strong fit), Tier 3 (qualified if other signals). List exclusions. |
| **BUSINESS MODEL** | ICP segments from context | This is often the KEY qualifying dimension. Detail each segment with bullet points. Include DISQUALIFY criteria. |
| **TECH STACK** | Current state + displacement targets | What prospects use today (the pain). What competitors to displace. What integrations you have. |
| **AD SPEND / KEY SIGNAL** | The single most important qualifying metric | Only include this row if there's a hard quantitative threshold (e.g., "$500K+/mo ad spend"). If the key signal is qualitative (e.g., "multi-entity complexity"), fold it into BUSINESS MODEL instead. |
| **REVENUE RANGE** | Revenue tiers from context | Map each tier to ACV. Include DISQUALIFY floor. |
| **FUNDING / OWNERSHIP** | Funding stages, PE signals | Prioritize by urgency (PE-backed > recent acquisition > VC-backed > family-owned). |
| **INTENT SIGNALS** | Sales triggers from context | List strong buying signals and pain signals. Prioritize accounts showing 2+ signals. Include timing guidance. |

**Rules:**
- `Qualified` column = the baseline criteria (who qualifies)
- `Prioritization` column = how to rank within qualified (tier ordering)
- Every row must cite its source: "SOURCE: company/context.md", "SOURCE: Call notes" or "SOURCE: Website research"
- Include verbatim quotes from the context file or calls where they add specificity
- DISQUALIFY criteria must be explicit (e.g., "Single entity = DISQUALIFY")
- If a dimension doesn't apply, omit it rather than forcing it

### Phase 4 — Build Sheet 2: Prospect Level

**Format:** 3-column table — `Lead Score Category` | `Qualified` | `Prioritization`

**Required rows (4 dimensions):**

| Row | Description | How to Fill |
|-----|-------------|-------------|
| **SENIORITY** | Decision-maker levels from context | Must vary by company size (e.g., CEO at SMB, CFO at mid-market, VP at enterprise). |
| **DEPARTMENT / JOB TITLE** | Titles from context + research | Split into PRIMARY BUYERS and SECONDARY (Influencers). Group by company size. |
| **LINKEDIN PROFILE KEYWORDS** | Keywords that indicate a good prospect | Split into MUST HAVE, STRONG SIGNALS, COMPETITOR KEYWORDS, TOOL KEYWORDS, INDUSTRY-SPECIFIC. |
| **LINKEDIN ACTIVITY SIGNALS** | Behavioral signals on LinkedIn | ENGAGEMENT PATTERNS (what they post/share/follow) and PRIORITIZE (highest-intent behaviors). |

**Rules:**
- Title targeting must map to company size segments (the buyer at a 30-person company differs from a 500-person company)
- LinkedIn keywords must include both role keywords AND industry-specific terms
- Activity signals must be specific and observable (not "seems interested in cash flow" — instead "posts about 13-week cash forecasting challenges")

### Phase 5 — Build Sheet 3: Persona Matrix

**Format:** 6-column table — `Persona` | `Level` | `KPIs` | `Related Challenges` | `Intent Signals` | `Related Benefits`

**Rules for persona creation:**
- Create **4-6 personas** based on the target titles in the context file
- Each persona must map to a specific company size segment where they're the primary buyer
- Personas should span the buying committee: decision maker, champion, influencer, day-to-day user

**For each persona, fill all 6 columns:**

| Column | What to Include |
|--------|----------------|
| **Persona** | Full title + role context (e.g., "CFO / VP Finance (Primary buyer at mid-market 50-500 employees)") |
| **Level** | Seniority band (C-Level, VP, Director, Manager, Senior IC) |
| **KPIs** | 5-7 measurable KPIs this person is evaluated on. Use bullet list format. |
| **Related Challenges** | 5-7 specific pain points your product solves. Write from the persona's perspective. |
| **Intent Signals** | 5-7 observable behaviors that indicate this persona is in-market. Must be specific and actionable. |
| **Related Benefits** | 5-7 benefits mapped 1:1 to the challenges. Write as value props, not features. |

**Quality checks:**
- Challenges and Benefits must mirror each other (every challenge has a corresponding benefit)
- KPIs must be things this specific role actually owns (not generic business metrics)
- Intent signals must be things you can actually observe on LinkedIn, job boards, or news
- Benefits must use the persona's language, not your own marketing copy
- Include pricing context where relevant (e.g., "affordable at $6-12K/yr vs $50K+ for enterprise tools")

### Phase 6 — Build Sheet 4: Signal Scoring

**Format:** 5-column table — `Signal Category` | `Criteria` | `Points` | `Max Points` | `Notes`

**Structure:**
- Total possible = **100 points**
- 4-6 signal categories, each with 3-5 criteria levels
- Must include tier thresholds at the bottom
- Must include a calibration note

**Standard categories and weight ranges:**

| Category | Weight Range | Guidance |
|----------|-------------|----------|
| **Key Qualifying Signal** | 25-40 pts | The single most important signal. Highest weight. Gets 0 (DQ) at bottom level. |
| **Funding / Ownership** | 15-20 pts | PE-backed, VC, bootstrapped. Higher = more urgency. |
| **Revenue Range** | 10-15 pts | Maps to ACV potential. |
| **Industry Fit** | 10-15 pts | Tier 1/2/3 verticals from Account Level sheet. |
| **Intent Signals** | 10-15 pts | Additive (+5 each). Multiple signals = higher score. |

**Identify the Key Qualifying Signal:**
- This is the single signal that, if absent, disqualifies the account
- It gets the highest point weight (25-40 points)
- The lowest level of this signal = 0 points and a (DQ) tag
- Examples:
  - A DTC creative tool: Ad spend ($500K+/mo = 40 pts, <$500K = 0 DQ)
  - A treasury / cash-management SaaS: Multi-entity complexity (10+ entities = 35 pts, 1 entity = 0 DQ)

**Tier thresholds (below the scoring rows):**

| Tier | Points | Treatment |
|------|--------|-----------|
| **Tier 1 (High Touch)** | 70+ | ABM, personalized outreach, multi-thread, custom offering |
| **Tier 2 (Multi-Channel)** | 45-69 | Multi-channel sequence, case-study-led outreach |
| **Tier 3 (Nurture)** | <45 | Nurture, re-evaluate quarterly |

**Rules:**
- Point allocations must be mutually exclusive within a category (pick the highest matching level)
- Intent signals are additive (can earn multiple +5s)
- DQ at any category = DQ regardless of total score
- Include "NOTE: Scoring thresholds need calibration against won/lost deals" at the bottom

### Phase 7 — Build Sheet 5: Case Study Reference

**Format:** 6-column table — `Company` | `Industry` | `ICP Segment` | `Multi-Entity Signal (or Key Signal)` | `Key Insight` | `Source`

**Three sections:**

1. **CASE STUDY COMPANIES (from website/research)** — Named clients found on the website, case studies, or logo bars. For each:
   - Identify their industry and which ICP segment they represent
   - Note the key qualifying signal (e.g., "35 entities across operations" or "$100M+ ad spend")
   - Write an insight explaining WHY this company validates the ICP
   - Cite the source (Website case study, Website logo bar, G2 review, etc.)

2. **DREAM CLIENTS (target domains from the context file)** — The dream accounts listed in `company/context.md`. For each:
   - Research enough to identify industry and ICP segment
   - Note the key qualifying signal
   - Explain why they're a dream client
   - Source = "company/context.md target domains"

3. **EXCLUDED COMPANIES (exclusions from the context file)** — The excluded domains with rationale. For each:
   - Note the industry
   - Mark as "EXCLUDED"
   - Explain the exclusion reason in the persona's context (e.g., "Only 1 bank, 1 entity — no operational pain")
   - Source = "company/context.md exclusions"

**Target counts:**
- 7-12 case study companies
- 5-10 dream clients
- 2-5 excluded companies (for calibration)

**Column 4 header adapts to your key signal:**
- If key signal is multi-entity complexity → "Multi-Entity Signal"
- If key signal is ad spend → "Est. Ad Spend" or "Spend Signal"
- If key signal is revenue → "Revenue Signal"
- Generic fallback → "Key Signal"

### Phase 8 — Generate the .xlsx Workbook

Use Python with `openpyxl` to create a styled workbook.

**Styling requirements:**
- **Header row**: Dark blue fill (`1F4E79`), white bold font, center-aligned
- **All cells**: Thin black borders, text wrap enabled, top-aligned
- **Column widths**: Auto-sized to content (minimum 20, maximum 80 for text-heavy columns)
- **Sheet names**: `Account Level`, `Prospect Level`, `Persona Matrix`, `Signal Scoring`, `Case Study Reference`

**Python template** (see `assets/xlsx-generator.md` for full code):

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = openpyxl.Workbook()
header_font = Font(name='Calibri', bold=True, color='FFFFFF', size=11)
header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
cell_alignment = Alignment(wrap_text=True, vertical='top')
thin_border = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)
```

### Phase 9 — Generate Per-Sheet .csv Files

After creating the .xlsx, export each sheet as a separate CSV:
- Read each sheet from the workbook
- Write to `{Company}_ICP_Matrix_{SheetName}.csv`
- Sheet name mapping: spaces → underscores (e.g., "Account Level" → "Account_Level")

### Phase 10 — Quality Review Checklist

Before delivering, verify:

- [ ] **Completeness**: All 5 sheets populated, no empty cells where data is expected
- [ ] **Source attribution**: Every Account Level row cites source (context file vs. research)
- [ ] **Key signal identified**: Signal Scoring sheet has a clear #1 weighted signal with DQ threshold
- [ ] **Persona coverage**: 4-6 personas spanning decision maker → day-to-day user
- [ ] **Challenges ↔ Benefits mirror**: Each persona's challenges map to corresponding benefits
- [ ] **Scoring totals 100**: Signal categories sum to exactly 100 max points
- [ ] **DQ criteria explicit**: At least 2-3 hard disqualification rules documented
- [ ] **Tier thresholds set**: 3 tiers with point ranges and treatment descriptions
- [ ] **Case studies validated**: Each case study company is real and verifiable
- [ ] **Dream clients from context**: Target domains actually appear in the Case Study sheet
- [ ] **Exclusions with rationale**: Excluded companies explain WHY they don't fit
- [ ] **No hallucinated data**: Every claim can be traced to the context file, website, or a web search result
- [ ] **Files saved correctly**: .xlsx + 5 .csv files in `company/` or `plays/<play-slug>/research/`

---

## Adapting to Different Business Types

The ICP matrix structure is universal, but the **content** adapts dramatically based on the business model. Key variations:

### Selling to B2C / DTC brands (e.g., a creative or ads tool)
- Key signal: **Ad spend threshold** (hard quantitative floor)
- Personas: Growth/marketing roles (VP Growth, Head of Paid, Creative Director)
- Industry dimension: Product verticals (Health & Wellness, Food & Bev, Beauty)
- Tech stack: Shopify, Meta Ads, TikTok Ads, Klaviyo
- Case studies: Include estimated ad spend per company

### B2B SaaS / Fintech (e.g., a cash-management platform)
- Key signal: **Operational complexity** (qualitative — multi-entity, multi-bank)
- Personas: Finance roles (CFO, VP Finance, Treasurer, Controller)
- Industry dimension: Operationally complex industries (Restaurants, Healthcare, Hospitality)
- Business model dimension becomes the MOST IMPORTANT row (PE-backed vs. multi-location vs. no-TMS)
- Case studies: Include entity count or complexity signal per company

### Services / Agency (e.g., an outbound agency)
- Key signal: **Growth stage + team size** (Series B+, $50M+ ARR, 50+ employees)
- Personas: Revenue leaders (VP Sales, CRO, Head of Growth)
- Industry dimension: Tech verticals with outbound-heavy GTM
- Case studies: Include growth metrics (ARR, headcount growth)

---

## Templates

- **[XLSX Generator Code](assets/xlsx-generator.md)**: Full Python script for workbook creation with styling
- **[Context Field Map](assets/context-field-map.md)**: Every `company/context.md` field → which matrix cell it feeds

## Tips

- **Context first, research second.** Always extract `company/context.md` completely before going to the web. This prevents research bias.
- **Identify the key qualifying signal early.** It determines the entire scoring model structure. Ask: "What single thing, if absent, means this account will never buy?"
- **Don't force 8 Account Level rows.** If a dimension doesn't apply (e.g., no hard ad spend threshold for a B2B company), omit it rather than adding a weak row.
- **Persona count scales with buying committee complexity.** Simple SMB sale = 3-4 personas. Enterprise with multiple stakeholders = 5-6 personas.
- **Case study section is ICP validation.** It proves the matrix works against real companies. If case studies contradict your matrix criteria, revise the matrix.
- **Excluded companies are as valuable as included ones.** They calibrate the floor — showing what ALMOST qualifies but doesn't.
- **Scoring thresholds are starting points.** Always note they need calibration against real won/lost data.
- **Column 4 in Case Study adapts.** Name it after whatever the key qualifying signal is for this specific ICP.

*Progressive disclosure: load assets/xlsx-generator.md and assets/context-field-map.md only when building the actual workbook.*

---
