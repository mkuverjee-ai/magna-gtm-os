---
name: signal-detection
description: 30 intent signals across 6 categories with reliability tiers and freshness rules. Use when building signal-based targeting.
---

> **Note:** the detection tools named below are examples from the wider market. In this OS,
> AI Ark (`ai-ark`) is the primary data source for companies, people and job changes, and Exa
> (`exa-search`) covers web signals. The signal logic, tiers and timing windows apply either way.

# Signal Detection

Intent signal detection and scoring system. 30 sales triggers across 6 categories, tiered by reliability, with timing windows and multi-signal stacking strategies.

---

## When to Use

- Identifying which intent signals to track for a play (`plays/<play-slug>/`)
- Setting up signal detection in AI Ark, Clay, or other enrichment tools
- Scoring and prioritizing accounts based on signal strength
- Deciding when to reach out based on signal freshness
- Stacking multiple signals for higher-intent targeting

---

## Signal Reliability Tiers

Not all buying signals are equal. Rank signals by correlation with actual purchase intent:

**Tier 1 — Highest Intent (Same-day outreach)**
- Funding announcement (Series A+)
- Expansion into new market/geography
- Leadership change in buyer's department

Budget is approved or about to be. Act fast.

**Tier 2 — Strong Intent (30-90 day window)**
- Competitor tech adoption
- Partnership or acquisition announcement
- Hiring surge in relevant department (5+ roles)

Investment is happening. Timing window is 30-90 days.

**Tier 3 — Moderate Intent (Nurture sequence)**
- Job postings (1-3 roles)
- Industry award or recognition
- Product launch or feature release

Activity is there, but intent is less urgent.

**Tier 4 — Weak Intent (Context only)**
- Social media activity
- Website traffic spikes
- General news mentions

Interesting context. Not a trigger on its own.

---

## The 30 Sales Triggers

### 1. Funding & Financial Signals

| # | Trigger | Detection Tool | Timing Window |
|---|---------|---------------|---------------|
| 1 | Series A+ Funding | Crunchbase, PredictLeads, Owler, PitchBook | 0-90 days post-announcement |
| 2 | Revenue Milestone | News monitoring, Serper | 30-60 days |
| 3 | IPO Filing/Preparation | SEC filings, Crunchbase | 60-180 days |
| 4 | M&A Activity | Crunchbase, PredictLeads, News | 30-90 days |
| 5 | New Investment Round | Clay + Intellizence (1 credit) | 0-60 days |

### 2. Hiring & Team Changes

| # | Trigger | Detection Tool | Timing Window |
|---|---------|---------------|---------------|
| 6 | New Executive Hire | LinkedIn (AI Ark/Clay), Sales Nav | Days 14-30 (first 90 days = open to ideas) |
| 7 | Hiring Surge (5+ roles) | LinkedIn Jobs, PredictLeads, Clay | 30-90 days |
| 8 | SDR/BDR Hiring | LinkedIn, PredictLeads | 14-60 days |
| 9 | Department Expansion | LinkedIn headcount data (1 credit) | 30-90 days |
| 10 | Champion Job Change | Clay, LoneScale, Champify | 0-30 days (act fast) |

### 3. Technology & Digital Signals

| # | Trigger | Detection Tool | Timing Window |
|---|---------|---------------|---------------|
| 11 | New Tech Adoption | BuiltWith, HG Insights, TheirStack | 30-90 days |
| 12 | Tech Stack Removal | BuiltWith, HG Insights | 0-30 days (they're shopping) |
| 13 | Website Redesign | Claygent + web scrape | 30-60 days |
| 14 | New Product Launch | News, Serper, Company blog | 14-60 days |
| 15 | Running LinkedIn Ads | Serper API (0 credits) | Active campaign = active budget |

### 4. Competitive & Vendor Intelligence

| # | Trigger | Detection Tool | Timing Window |
|---|---------|---------------|---------------|
| 16 | Negative G2/Capterra Reviews | Zenrows + G2/Capterra (3 credits) | 0-90 days |
| 17 | Competitor Contract Expiry | PredictLeads, intent data | 60-90 days before renewal |
| 18 | Competitor Downgrade/Churn | BuiltWith (tech removal) | 0-30 days |
| 19 | Pricing Page Visits (if your tool) | RB2B, Common Room, Vector | 0-7 days |
| 20 | Comparison Shopping (review sites) | G2 buyer intent, 6sense | 7-30 days |

### 5. Product & Business Events

| # | Trigger | Detection Tool | Timing Window |
|---|---------|---------------|---------------|
| 21 | Geographic Expansion | News, LinkedIn, PredictLeads | 30-90 days |
| 22 | New Office/Location | News, Google Maps | 30-90 days |
| 23 | Regulatory Change Impact | Industry news, Serper | 0-60 days |
| 24 | Conference/Event Attendance | Event sites, LinkedIn, scraping | 14 days before to 7 days after |
| 25 | Partnership Announcement | News, LinkedIn posts | 14-60 days |

### 6. Marketing & Reputation Signals

| # | Trigger | Detection Tool | Timing Window |
|---|---------|---------------|---------------|
| 26 | LinkedIn Post Engagement | Clay, Trigify, Teamfluence | 0-7 days |
| 27 | Content Topic Shift | Company blog monitoring | 30-60 days |
| 28 | Award/Recognition | News, Serper | 14-30 days |
| 29 | PR/Media Mention | Serper, Google News | 7-30 days |
| 30 | Community Engagement | PhantomBuster, Clay | 0-14 days |

---

## Signal Freshness Rules

| Signal Type | Fresh Until | Optimal Outreach Window |
|-------------|-------------|------------------------|
| Funding news | 90 days | Weeks 2-8 post-announcement |
| Series C deployment | 180 days | Weeks 5-12 (budget allocation phase) |
| LinkedIn posts | 30 days | 0-7 days |
| Hiring activity | 60 days | 14-30 days |
| G2 reviews | 90 days | 0-30 days |
| Negative reviews | 180 days | 0-60 days |
| New exec hire | 90 days | Days 14-30 |
| Tech stack change | 60 days | 0-30 days |
| Champion job change | 30 days | 0-14 days (fastest decay) |
| Event attendance | 21 days | 7 days before to 7 days after |

---

## Multi-Signal Stacking

Blend at least two independent signals before green-lighting high-effort plays.

**Tier 1 + Tier 1 = White-glove (Immediate outreach)**
- Funding + Hiring surge = Budget approved AND deploying
- New exec + Tech removal = New decision-maker AND shopping
- Champion job change + ICP fit = Warm contact at new company

**Tier 2 + Tier 2 = Solid/Scalable (Priority sequence)**
- Hiring (1-3 roles) + LinkedIn engagement = Active and receptive
- Competitor review + Website visit = Shopping and considering you
- Industry news impact + Geographic expansion = Urgency and growth

**Tier 3 = Templated Nurture**
- Social activity + Industry mention = Aware but not ready
- Award + General hiring = Healthy company, low urgency

---

## Using Signals in Campaign Copy

**Trigger-based openers** — reference the signal directly:
- "Saw [Company] just closed your Series B — congrats."
- "Noticed you're hiring 5 SDRs — scaling outbound?"
- "Your team just dropped [Competitor] from the stack..."

**Timing references** — show you know where they are:
- "Most teams 6-8 weeks post-funding start evaluating..."
- "New VPs in months 1-3 typically audit existing tools..."

**The "So What?" test** — every signal reference must pass:
1. Is it recent?
2. Does it connect to my offer?
3. Would they care that I noticed?
4. Can I tie it to a specific pain?

If mentioning job postings, go deeper than the obvious. "You're hiring SDRs" is table stakes. "You're hiring SDRs but don't have a rev ops lead yet" shows actual insight.

---

## Detection Tools Quick Reference

| Tool | Best For | Cost |
|------|----------|------|
| Serper | News, LinkedIn ads, general signals | 0 credits |
| Clay Signals | Hiring, funding, tech changes | 1 credit |
| PredictLeads | Job openings, funding, partnerships | Via Clay |
| BuiltWith / HG Insights | Tech stack adoption and removal | Via Clay |
| G2 / Capterra | Competitor reviews, buyer intent | 3 credits (via Zenrows) |
| LinkedIn / Sales Nav | People moves, engagement, hiring | 1 credit |
| LoneScale / Champify | Champion job changes | Dedicated tool |
| Crunchbase / PitchBook | Funding, M&A, IPO filings | Dedicated tool |

---

## Tips

- Track signal-to-meeting conversion rate, not just detection volume
- Automate Tier 1 signals with same-day outreach triggers; batch Tier 3-4 into weekly sequences
- If after 10 minutes of research you find no Tier 1/2 signals, skip or use a Whole Offer strategy
- Cost optimization: use Serper (0 credits) for news, LinkedIn (1 credit) for hiring/company data, save 3-credit tools for qualified accounts
- Use 1st-party data (CRM, product usage, website visitors) alongside 3rd-party signals for the strongest stacking combos
