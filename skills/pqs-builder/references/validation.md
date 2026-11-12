# Validation: gates, counts, the five-row audit and the customer backtest

A segment is a hypothesis until it has a count, a checked sample and a backtest. This file is how to
get each one, and what to do when it fails.

---

## The eight gates (phase 4)

| # | Gate | Pass example | Fail example | On fail |
|---|---|---|---|---|
| Q1 | Hyper-specific | "SDR role posted on or after 28 Jul 2026" | "recently hiring" | kill, rewrite with a field and threshold |
| Q2 | Factually grounded | "AI Ark people, latest_title ~ RevOps, count == 0" | "probably has no RevOps" | kill |
| Q3 | Non-obvious | "MDS estates outside the partner's own customer list" | "mid-market SaaS in the US" | narrow |
| Q4 | Situation, not trait | "posted a second BDR role in 60 days" | "has a sales team" | reframe as an event |
| Q5 | Tension present | hiring reps **and** nobody runs them | hiring reps | kill, find H2 |
| Q6 | Copy-safe opener | "your BDR ad from 18 Aug" | "congrats on the Series B" as the only hook | reframe the opener |
| Q7 | Addressable | 300 to 20,000 companies | 8 companies, or 400,000 | narrow, or go 1:1 |
| Q8 | Fits the offer | you sell the fix | real pain, you sell something else | kill |

Q1, Q2, Q5, Q8 kill. The rest send it back.

## 1. Count it

- Use free or near-free counts first: Freckle `--preview` (free), AI Ark preview via
  `aiark.py preview` (1 credit/page) and read the total, your own past pulls in `plays/*/leads/`.
  Never size with a paid search.
- Count **each condition alone, then together.** That shows which condition narrows the list, and
  catches the one that silently empties it.
- Record: the number, the exact query, the source, the date. A count without its query cannot be rebuilt.
- AI Ark caps a query at 10,000 rows. To count past that, slice by country and headcount band and sum.
- Bands: under ~30 = 1:1 by hand; ~300-20,000 = a segment; over ~50,000 = still a firmographic.

## 2. The five-row audit

Pull 5 accounts the test says are in. For each, open the evidence yourself and answer: **is this company
really in this situation today?**

| Row | Each condition true? | Evidence still live? | In the situation? | Why not |
|---|---|---|---|---|

- 5 of 5 or 4 of 5: proceed.
- 3 of 5: tighten the condition that failed, re-pull, re-audit.
- 2 or fewer: the membership test is wrong. Back to phase 3.

Measured failure rates, so nobody assumes a clean list:
- A growing-SDR Exa run: 49 rows returned, 19 had an SDR
  manager, RevOps or GTM engineer (failing the "no system" condition), 5 postings had closed. 25 usable.
- A rule-based fit list over CRM fields: 27% wrong on 100 accounts checked (franchise brands,
  carmakers, banks, a pension fund, a company in creditor protection).

Note *why* rows fail. The failure reason is usually the missing exclusion.

## 3. The customer backtest (lift)

The question: **were your real customers in this situation before they bought, more often than
random companies in your market?**

1. Take your last 20-50 closed-won accounts with close dates (read-only from the CRM, or an export).
2. For each, check the membership test **as of the 90 days before the close date**. Job posts, filings,
   hires and tech first-seen dates are usually dated, so this works for most fingerprints. Mark
   `unknown` when the history cannot be checked; never guess.
3. Do the same on a random sample of the same size from your TAM (same date window).
4. Lift = share of customers in the segment / share of the random sample in the segment.

| Lift | Read |
|---|---|
| Over ~3x | Strong. The situation predicts buying |
| ~2-3x | Real, worth running |
| Under ~2x | The segment is mostly describing the market. Narrow it or drop it |
| Customers ~0% | You win somewhere else. Check closed-lost: maybe this is where you lose |

Also run it on **closed-lost**. A segment that over-indexes on losses is an exclusion.

Small numbers: with 20 customers, one company is 5 points. Report the raw counts ("7 of 20 vs 2 of 20"),
not only the ratio.

No customer data: use the seed companies from the calls or replies and call it a **seed check**. It shows the
situation is real; it does not show it predicts buying.

## Cost discipline

- Free: counts, public pages, job pages, DNS lookups (MX, SPF, DMARC), company sites.
- Paid or more than 10 rows: show the estimated cost and get an explicit OK first.
- Exa Agent: measured ~$0.39 per row returned and ~$0.76 per usable row on the growing-SDR run ($19.06
  for 49 rows at ultra effort). Split big runs by geography instead of asking one run for 150.

## Status labels

| Label | Means |
|---|---|
| `measured` | counted, 5-row audit passed, backtest (or seed check, labelled) done |
| `partly measured` | name what is missing |
| `hypothesis` | gated, not yet counted or audited |
| `belief-led` | built from the team's beliefs with no buyer-side calls, replies or customer data |

Every segment in the shipped doc carries one. Nothing is presented as measured that was not.
