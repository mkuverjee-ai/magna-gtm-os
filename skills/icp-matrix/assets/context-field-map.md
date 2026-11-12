# Company Context → ICP Matrix Field Map

This maps every field in `company/context.md` to the specific cell(s) it populates in the ICP matrix.
If the context file is missing a field, add it there first; the matrix should never be the only place a fact lives.

## Context Section → Matrix Sheet Mapping

### Company Overview Section

| Context Field | Matrix Sheet | Matrix Row/Column | Notes |
|------------|-------------|-------------------|-------|
| Company Name | All sheets | Used in file naming and headers | `{Company}_ICP_Matrix.xlsx` |
| Company Summary | Persona Matrix | Related Benefits (framing) | Sets the value prop language for all personas |
| Core Problem | Persona Matrix | Related Challenges | The master pain point — decompose into persona-specific versions |
| Unique Solution | Persona Matrix | Related Benefits | How the product solves the core problem |
| Pricing Tiers | Account Level | REVENUE RANGE → Prioritization | Maps revenue tiers to ACV: "$50M-$500M rev → $25K-$50K/yr ACV" |

### Target Market Section

| Context Field | Matrix Sheet | Matrix Row/Column | Notes |
|------------|-------------|-------------------|-------|
| Target Countries | Account Level | LOCATION / GEOGRAPHY | Direct mapping. Note if other geos handled by other teams |
| Target Industries | Account Level | INDUSTRY / VERTICAL → Qualified | List verbatim. Research to add Tier 1/2/3 ranking |
| Excluded Industries | Account Level | INDUSTRY / VERTICAL → Qualified (exclusions) | List under "EXCLUDE:" section |
| Min Employees | Account Level | EMPLOYEE COUNT → Qualified (floor) | Note when headcount is a weak signal |
| Max Employees | Account Level | EMPLOYEE COUNT → Qualified (ceiling) | |
| Revenue Range Tags | Account Level | REVENUE RANGE → Qualified | May have gaps (e.g., context says "$10-50M, $100-500M" — check if $50-100M is intentional gap) |
| ICP Description | Account Level | BUSINESS MODEL → Qualified | **CRITICAL** — this defines the ICP segments. Often the longest field. |
| Target Domains (Dream Clients) | Case Study Reference | DREAM CLIENTS section | Research each domain to fill Industry, ICP Segment, Key Signal |
| Excluded Domains | Case Study Reference | EXCLUDED COMPANIES section | Include the exclusion rationale from the context file |
| Max Target Companies | — | Not in matrix | Informs target-list sizing later, not ICP definition |

### Target Personas Section

| Context Field | Matrix Sheet | Matrix Row/Column | Notes |
|------------|-------------|-------------------|-------|
| Target Titles | Prospect Level | SENIORITY + DEPARTMENT | Split by decision maker vs. influencer vs. entry point |
| Target Titles | Persona Matrix | Persona (column 1) | Each unique title becomes a persona row |
| Job Function | Prospect Level | DEPARTMENT / JOB TITLE | Usually "Finance", "Marketing", "Growth", etc. |
| Seniority Levels | Prospect Level | SENIORITY → Qualified | "C-Level, VP, Director, Manager" |

### Sales Context Section

| Context Field | Matrix Sheet | Matrix Row/Column | Notes |
|------------|-------------|-------------------|-------|
| Sales Trigger Tier 1 | Account Level | INTENT SIGNALS → Qualified | Highest priority triggers |
| Sales Trigger Tier 2 | Account Level | INTENT SIGNALS → Qualified | Secondary triggers |
| Sales Trigger Tier 3 | Account Level | INTENT SIGNALS → Qualified | Tertiary triggers |
| Sales Trigger Tier 1 | Signal Scoring | INTENT SIGNALS category | Tier 1 triggers get +5 points each |
| Competitors | Account Level | TECH STACK → Qualified (displacement targets) | Also feeds Prospect Level → LINKEDIN PROFILE KEYWORDS (competitor keywords) |
| Competitors | Signal Scoring | Notes column | Reference competitors in displacement context |

### Call Notes / Win-Loss

| Call Notes Field | Matrix Sheet | Matrix Row/Column | Notes |
|-------------------|-------------|-------------------|-------|
| Revenue range refinements | Account Level | REVENUE RANGE | Overrides the context file if more specific (e.g., context says "$10-50M" but calls say "$25M-$1B"); then update the context file |
| ACV targets | Account Level | REVENUE RANGE → Prioritization | Maps revenue tiers to deal sizes |
| Segment priorities | Account Level | BUSINESS MODEL → Prioritization | Which ICP segment to prioritize |
| Competitive positioning | Account Level | TECH STACK | How you position vs. competitors |
| Geographic scope | Account Level | LOCATION / GEOGRAPHY | May narrow or expand from context |

## Fields That DON'T Come From the Context File

These must be filled through research:

| Matrix Cell | Research Source |
|-------------|---------------|
| Account Level → TECH STACK (prospect's current tools) | Website integrations page, G2 comparisons, web search |
| Account Level → FUNDING / OWNERSHIP | Crunchbase, PitchBook, web search |
| Prospect Level → LINKEDIN PROFILE KEYWORDS | Inferred from personas + industry + competitor names |
| Prospect Level → LINKEDIN ACTIVITY SIGNALS | Inferred from persona pain points + industry communities |
| Persona Matrix → KPIs | Role-specific research + industry standards |
| Persona Matrix → Intent Signals | Observable behaviors on LinkedIn, job boards, news |
| Signal Scoring → Point weights | Derived from context emphasis + research on what matters most |
| Case Study Reference → CASE STUDY COMPANIES | Website logos, case studies, G2, press mentions |
