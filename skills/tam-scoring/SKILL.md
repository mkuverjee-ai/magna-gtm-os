---
name: tam-scoring
description: Build 80-100 point scoring models and tier a company list. Use when scoring a TAM into T1-T4.
---

# TAM Scoring

Build and run scoring models to tier company lists (usually a `skills/ai-ark/aiark.py companies` CSV) into campaign-ready, prioritized segments.

---

## Overview

A TAM scoring model assigns every company a numeric score based on observable data signals, then buckets them into tiers for campaign prioritization. Good models typically run 80-100 points across 4-6 signal groups.

---

## Standard Tier Thresholds

| Tier | Score Range | Action |
|------|-------------|--------|
| **Tier 1** | 65+ | Top priority. Send first. Best personalization. |
| **Tier 2** | 50-64 | Strong fit. Send second wave. |
| **Tier 3** | 35-49 | Marginal fit. Consider for volume plays only. |
| **DQ** | <35 | Disqualified. Do not send. |

Adjust thresholds based on total point scale. For an 85-point model, T1 might start at 65. For a 100-point model, T1 at 65-70.

---

## Common Signal Groups

### 1. Scale (10-25 pts)
What it measures: company size via employee count.

```
10,000+     → 25 pts (true enterprise)
5,000-9,999 → 20 pts
2,000-4,999 → 15 pts
500-1,999   → 10 pts
50-499      → 5 pts
<50         → 0 pts
```

Adjust ranges to match your ICP. A product selling to SMBs would invert this.

### 2. Revenue (15-20 pts)
What it measures: annual revenue as a proxy for budget.

```
$50M-$500M  → 20 pts (sweet spot for many mid-market products)
$25M-$50M   → 15 pts
$500M-$1B   → 10 pts
$10M-$25M   → 8 pts
$1B+        → 5 pts (too big, long sales cycle)
<$10M       → 0-5 pts
```

Revenue data from any B2B database (AI Ark, Apollo, etc.) is estimated for private companies. Treat it as directional, not exact.

### 3. Industry (10-15 pts)
What it measures: fit with your target verticals.

```
Tier 1 industries (core ICP)    → 15 pts
Tier 2 industries (adjacent)    → 10 pts
Tier 3 industries (stretch)     → 5 pts
Unknown                         → 5 pts (don't punish missing data)
Excluded industries             → -100 pts (auto-DQ)
```

Define excluded industries explicitly (e.g., non-profits, government, IT staffing).

### 4. Complexity / Specialization (15-30 pts)
This is the ICP-specific signal, usually the Key Qualifying Signal from `skills/icp-matrix`. Examples:

- **Multi-location count** (a cash-management SaaS): 10+ locations = 30 pts, 5-9 = 20, 2-4 = 10
- **Marketing org complexity** (an AI-visibility analytics tool): market count + regional marketing teams
- **Tech stack signals**: uses competitor tool, uses complementary tools
- **Digital maturity**: organic traffic, paid spend, website sophistication

### 5. Ownership / PE Backing (10-20 pts)
Relevant when you sell to PE-backed companies.

```
PE-backed confirmed   → 20 pts
Subsidiary of PE firm → 15 pts
VC/Growth equity      → 10 pts
Unknown               → 5 pts
Founder/Non-profit    → 0 pts
```

### 6. Bonus Signals (5-10 pts)
Optional accelerators:

- Franchise HQ = +5 pts
- Cash flow / treasury keywords in description = +5 pts
- Rapid growth signals = +5 pts
- Recent funding = +5 pts
- Hiring for relevant roles = +5 pts

---

## Data Quality Cleanup (Run Before Scoring)

### Step 1: Remove Bogus Entries
```python
BOGUS_NAMES = {"local my business", "google ai plugin", "auto-entrepreneur"}
BOGUS_SUBSTRINGS = ["follow us", "test account"]

def is_bogus(name):
    lower = name.strip().lower()
    if lower in BOGUS_NAMES:
        return True
    return any(sub in lower for sub in BOGUS_SUBSTRINGS)
```

### Step 2: Remove Slug Franchises
Franchise office entries that look like `keller-williams-realty-dpr`:
```python
def is_slug_franchise(name):
    return bool(re.match(r'^[a-z][a-z0-9-]+-[a-z0-9-]+$', name)) and len(name) > 10
```

### Step 3: Flag Suspect Data
```python
def flag_data_quality(name, employees, revenue):
    flags = []
    if employees > 200_000 and revenue > 200_000_000_000:
        flags.append("SUSPECT: extreme values -- verify manually")
    return flags
```

### Step 4: Deduplicate by Company Name
Keep the highest-scored entry when duplicates exist:
```python
best = {}
for company in scored:
    name = company['name'].strip().lower()
    if name not in best or company['score'] > best[name]['score']:
        best[name] = company
unique = list(best.values())
```

---

## Python Scoring Script Pattern

```python
import csv
import re

# A CSV from `aiark.py companies --out ...` (columns: company_name, headcount,
# annual_revenue, industry, description, ...). Rename the row.get() keys below
# if your export comes from somewhere else.
INPUT_FILE = "plays/<play-slug>/leads/companies/tam.csv"
OUTPUT_FILE = "plays/<play-slug>/leads/companies/tam_scored.csv"

def parse_number(val):
    if not val or val.strip() == "":
        return 0
    try:
        return float(val.strip().replace(",", ""))
    except ValueError:
        return 0

def score_company(row):
    total = 0
    breakdown = []

    # 1. Scale
    pts, reason = score_scale(parse_number(row.get('headcount', 0)))
    total += pts
    breakdown.append(f"Scale: {pts} ({reason})")

    # 2. Revenue
    pts, reason = score_revenue(parse_number(row.get('annual_revenue', 0)))
    total += pts
    breakdown.append(f"Revenue: {pts} ({reason})")

    # 3. Industry
    pts, reason = score_industry(row.get('industry', ''))
    total += pts
    breakdown.append(f"Industry: {pts} ({reason})")

    # 4. ICP-specific signal
    pts, reason = score_custom(row)
    total += pts
    breakdown.append(f"Custom: {pts} ({reason})")

    # DQ check
    if any("EXCLUDED" in b for b in breakdown):
        return -1, "DQ", breakdown

    # Tier assignment
    if total >= 65:
        tier = "Tier 1"
    elif total >= 50:
        tier = "Tier 2"
    elif total >= 35:
        tier = "Tier 3"
    else:
        tier = "DQ"

    return total, tier, breakdown

# Main: load -> clean -> score -> dedup -> sort -> export
with open(INPUT_FILE, 'r') as f:
    reader = csv.DictReader(f)
    rows = [r for r in reader if not is_bogus(r.get('company_name', ''))]

scored = []
for row in rows:
    score, tier, breakdown = score_company(row)
    row['Score'] = score
    row['Tier'] = tier
    row['Breakdown'] = ' | '.join(breakdown)
    scored.append(row)

# Dedup by company name (keep highest score)
best = {}
for row in scored:
    name = row['company_name'].strip().lower()
    if name not in best or row['Score'] > best[name]['Score']:
        best[name] = row

# Sort by score descending, export
final = sorted(best.values(), key=lambda x: -x['Score'])
# Write to CSV...
```

---

## Real Example 1: 80-Point Multi-Location Model

**Seller:** Cash flow management SaaS for mid-market
**Sweet spot:** $25M-$500M revenue, 10+ locations, ICP industries

| Signal Group | Max Points | Scoring Logic |
|-------------|-----------|---------------|
| Location Count | 30 | 20-49 locs (30), 50-99 (28), 100-199 (22), 10-19 (20) |
| Revenue | 20 | $50M-$500M (20), $25-50M (15), $500M-$1B (10) |
| Industry | 15 | Hospitality/Restaurants (15), Healthcare/Auto (12), RE/Construction (10) |
| Employees | 10 | 50-999 (10), 1K-5K (8), 10-49 (5) |
| Franchise Bonus | 5 | Franchise HQ = 5 |

**Results:** 3,010 companies scored. T1: 1,100 (36.5%), T2: 1,552 (51.6%), T3: 285 (9.5%), DQ: 73 (2.4%).

**DQ rules:** Tech vendors excluded, 5K+ locations with $5B+ revenue (data error), confirmed single location with no multi-loc signals.

**Location detection:** Regex patterns against company description + the database's locations field. Falls back to keyword signals (franchise, multi-site, nationwide) when no count available.

---

## Real Example 2: 85-Point B2C Enterprise Model

**Seller:** AI visibility analytics for B2C brands
**Sweet spot:** 500+ employees, $100M+ revenue, multi-market presence

| Signal Group | Max Points | Scoring Logic |
|-------------|-----------|---------------|
| Scale (employees) | 25 | 10K+ (25), 5K-10K (20), 2K-5K (15), 500-2K (10) |
| Revenue | 20 | $1B+ (20), $500M-$1B (18), $100M-$500M (14) |
| Marketing Complexity | 20 | Market count (0-12) + regional marketing teams (0-8) |
| Digital Maturity | 20 | Organic traffic (0-12) + paid spend (0-8) |

**Results:** 2,111 companies scored. Data cleanup removed bogus entries and slug-style franchise offices before scoring.

**Key difference from Example 1:** No industry scoring (replaced with Marketing Complexity after sales feedback that industry did not predict fit). Removed Talent & Intent category (no data available).

---

## How to Build a New Scoring Model

1. **Read `company/context.md` and recent sales calls** -- understand who buys and why
2. **Identify 4-6 signal groups** from the ICP matrix
3. **Allocate points** -- total should be 80-100. Weight toward the most differentiating signal.
4. **Define thresholds** -- aim for 30-40% Tier 1, 40-50% Tier 2, 10-15% Tier 3, <5% DQ
5. **Pull a sample** -- score 50 companies manually first
6. **Calibrate** -- adjust point ranges until the tier distribution looks right
7. **Review the sample with sales** -- get agreement before scoring the full list
8. **Score full list** -- run the Python script
9. **Export per-tier CSVs** -- separate files for T1, T2, T3 + DQ, in the play's `leads/companies/`

---

## Tips

- Always include a `Breakdown` column showing how points were allocated. It makes the model reviewable and debuggable.
- Export separate per-tier CSVs alongside the master file.
- Unknown data should get a small score (3-5 pts), not zero. Do not punish missing data too harshly.
- DQ rules should be explicit (excluded industries, data errors, confirmed bad fit).
- Re-run the scorer when new enrichment data arrives (e.g., PE backing added later).
- Database revenue is unreliable for private companies under $10M. Use employee count as the primary scale signal for smaller companies.

---

## References

- Keep each play's scoring script next to its output: `plays/<play-slug>/leads/companies/score_<play-slug>.py`.
- Record the final model (groups, points, thresholds, tier distribution) in `plays/<play-slug>/research/`.
