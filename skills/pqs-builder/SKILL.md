---
name: pqs-builder
description: >
  Build Pain-Qualified Segments (PQS) for your own outbound from everything you know: your sales and
  discovery call transcripts (if you record calls), closed-won and closed-lost data, CRM exports, the
  ICP and positioning in company/context.md, your website, and the replies your campaigns already got.
  Produces ranked, buildable segments: the situation and its tension, a field-level membership test,
  a measured count, real sample rows with evidence, a backtest against your own customers, a
  Clay/Exa/AI Ark build spec, and an opener in the buyer's own words. Use when someone says "build
  PQS", "what segments should we go after", "who is in pain", "turn these calls into segments", "is
  this a real segment", "find me a better list than firmographics", or before running /pvp-builder.
---

# PQS Builder: segments you can prove, build and send to

A pain-qualified segment is **a group of companies defined by a situation they are in right now,
proven from data, that someone on the team can rebuild next month from the spec alone.** It is the
list behind the message. Get it right and the copy mostly writes itself; get it wrong and no copy
saves it.

This skill produces the segments. `/pvp-builder` (same folder level, `../pvp-builder/`) turns the
best of them into gifts. Run this one first; pvp-builder picks up its output.

Each segment you decide to run becomes a **play**: `plays/<play-slug>/` with `research/`,
`leads/companies/`, `leads/contacts/`, `campaigns/` and `reports/`. Company-wide context (ICP,
positioning, proof, personas, offers) lives in `company/context.md`.

The theory is Jordan Crawford's (pain segments, PQS, existential data point, Texada test).
`references/segment-anatomy.md` is a distillation in our own words. If you have your own Edge Copilot
license (per person), `/edge pqs` pulls his current take. **Never paste Edge content into files in this
repo**: it is licensed per person and fingerprinted.

## The three sentences everything hangs off

1. **A segment is something that happened to them, not something they are.** "Series B fintech, 100-500
   staff" is a firmographic everyone already has. "Hired a second SDR in the last 60 days with nobody
   running the SDR team" is a situation, and it decays.
2. **Pain lives in a tension, not a signal.** One signal is noise (every vendor fires on "hiring
   SDRs"). Two facts pulling against each other is the pain: adding reps *and* no system for them.
3. **A segment is only real if the next person can rebuild it.** Every condition is a named source and
   field, the count is measured, and five real rows have been checked by eye. If any of those is
   missing, it is still a hypothesis, and the doc says so.

---

## Workflow

```
0 INTAKE       gather + tag every source                      -> context pack (shared with pvp-builder)
1 MINE         calls / replies -> buying moments + language     -> moments table + language bank
2 DRAFT        moments -> tension + amplifier + EDP              -> 6-12 candidate segments
3 FINGERPRINT  each condition -> source.field.operator           -> membership test per segment
4 GATE         Texada x3 + decay + copy-safety + addressability  -> survivors
   CHECKPOINT  show the user, wait for corrections
5 VALIDATE     count, 5 real rows audited, backtest on customers -> measured segments
6 SPEC         scoring, build recipe, Claygent/Exa prompt, refresh cadence
7 MESSAGE      PQS opener in their words + skeptical-buyer pass on the inference
8 SHIP         PQS doc + segments CSV + handoff to /pvp-builder
```

Each phase has a **reject state**. When a phase fails, go back a phase. Never patch a weak segment
with better copy.

### Phase 0: Intake

If a context pack already exists (`plays/<play-slug>/research/pvp/context-pack.md`, or
`research/pvp/context-pack.md` at the repo root for company-wide work), reuse it and add to it.
Otherwise build it with `../pvp-builder/templates/context-pack.md`, searching in this order:

- `company/context.md` (`python3 gtm.py company` prints it plus which keys are set). If a section is
  marked as a draft or unverified, say so and treat it as unverified.
- Existing plays: `plays/*/research/`, `plays/*/campaigns/` and `plays/*/reports/`
- `python3 gtm.py intel` (what already worked or failed: never re-propose a disproven segment)
- **Calls, if you record them:** `python3 gtm.py meetings [--limit N]`, then
  `python3 gtm.py transcript --date YYYY-MM-DD` for each one you need. Anything missing from your
  database: the `fireflies-mcp` skill. Recordings may be confidential; pull only what the task needs.
- **Your own campaign results, read-only** (keys via `gtm.cred("INSTANTLY_API_KEY")` /
  `gtm.cred("LEMLIST_API_KEY")`): analytics per campaign and the actual reply bodies. Real replies
  are the best buyer language you have, and "what got a yes" is the strongest evidence of an offer
  that works (one measured programme: ~9,500 sends, 1 positive, and that one asked for a profit
  forecast). Reading is fine; this skill never creates, loads or sends.
- Your own competitor comparison docs: verify every competitor claim on the **competitor's own public
  pages** before it goes in copy (comparison matrices go stale, especially on pricing).
- Your website: home, product, pricing, customers/case studies, about, careers
- **Your customer data.** Closed-won and closed-lost with dates and reasons, from a CRM export or a
  read-only API. This is what phase 5 backtests against, so pull it early.

Every line carries a source tag. Unsourced = `[ASSUMPTION]`. Unknown = `[SLOT: ...]`. **Never write
positioning, customers or numbers from background knowledge.**

Kinds of evidence are worth different things. Say which you have:

| Evidence | What it gives you | Weight |
|---|---|---|
| **Your sales and discovery calls with prospects** | Why buyers buy, in the buyers' words | Highest. This is the ground truth |
| Closed-won notes / win-loss interviews | The moment of purchase | High |
| **Replies to your campaigns** | Unprompted buyer language, what got a yes and what got a no | High, and available even when no calls are recorded |
| Customer list with close dates (no notes) | Who bought and when, for the backtest | High for phase 5 |
| Internal strategy calls, the ICP in `company/context.md`, positioning docs | What the team *believes* about its buyers | Useful, but a belief. Mark it `[team belief]` until data agrees |

**No transcripts?** Call recordings are often sparse or confidential. The skill still works: mine the
campaign replies, closed-won/lost notes and the customer list in phase 1 instead, run the customer
backtest in phase 5 as the main proof, and label segments `belief-led` until the backtest agrees.

### Phase 1: Mine the calls (and replies)

Goal: for every prospect or customer conversation, **what was true at the moment they decided to talk
or buy**, in their words. `references/call-mining.md` has the extraction schema, the subagent prompt
and the batching rules. The same schema works on reply threads and win-loss notes.

- More than ~15 transcripts: fan out to subagents in batches of ~20, one schema, notes saved to
  `plays/<play-slug>/research/pqs/mining/batch-N.md` (or `research/pqs/mining/` for company-wide
  work). Under 15: read them yourself.
- Pull, per conversation: the situation, the *why now*, what they already tried, verbatim pain lines
  with the speaker, and the **outside-in fingerprint** (what a stranger could have seen beforehand: a
  job post, a filing, a tool, an ad, a hire).
- Build the **language bank**: the exact phrases buyers used for the pain, with who and when. This
  becomes the opener in phase 7.
- Count. "Came up in 12 of 100 calls" is a finding; "came up a lot" is not.

Reject state: no buyer-side conversations and no customer data means you are working from the team's
beliefs. Continue, but every segment is marked `belief-led` and phase 5's backtest becomes mandatory
before anything ships.

### Phase 2: Draft candidate segments

Cluster the buying moments into **6-12 candidate segments**. For each, write the anatomy
(`references/segment-anatomy.md`):

- **Situation**, one sentence a ten-year-old understands
- **Tension**: H1 (the thing they are doing) pulling against H2 (the thing that makes H1 hurt)
- **Amplifier**: the deadline, target, season or regulation that makes it hurt *now*
- **Existential data point (EDP)**: the number that, past a threshold, costs someone their job, the
  quarter or a contract. If you can only find an efficiency gain, the segment is incremental. Say so;
  it can still run, but it must be sold harder
- **Evidence**: which calls / replies / customers, with counts
- **Who feels it**: the title that owns the pain, and whether that person can sign (in one measured
  set of B2B sales calls, 8 of 19 champions could not, so note the forward path)

Write the softer variant too when the evidence is a pattern rather than a proof.

### Phase 3: Fingerprints: the membership test

For every condition in every segment, write one line:

```
condition         | source                  | field / query                          | operator     | public? | cost
existing team     | LinkedIn via AI Ark     | people, latest_title ~ SDR|BDR, current | count >= 1   | yes     | 1 credit/page
hiring more       | job boards (Exa/Clay)   | title ~ SDR|BDR|AE, posted_at          | >= 2026-07-28| yes     | ~0.39 USD/row (Exa, measured)
no system         | AI Ark people           | title ~ SDR manager|RevOps|GTM eng     | count == 0   | proxy   | 1 credit/page
```

Mark each condition **public / proxy / not public**:
- **public**: the field states it directly.
- **proxy**: the field suggests it (tech first-seen date as a guess at a contract anniversary). Proxies
  are for scoring and for asking. Never state one as fact in copy.
- **not public**: drop it from the test, and turn it into a qualifying question for the call.

Where pain leaves fingerprints, with measured costs and traps: `../pvp-builder/references/data-sources.md`
(AI Ark first; then Exa, Ocean, Apify, Freckle, Clay CLI, and free public records).

Reject state: a segment whose core tension rests on a not-public condition is a discovery question, not
a segment. Move it to "questions for the call" and drop it from the list.

### Phase 4: Gate

`references/validation.md` has the full gates. Pass/fail each, with the reason:

| # | Gate | Fails when |
|---|---|---|
| Q1 | **Hyper-specific** | "recent", "growing", "many"; a condition with no field and threshold |
| Q2 | **Factually grounded** | a condition you cannot name a source field for |
| Q3 | **Non-obvious** | the segment is a firmographic your competitors also target |
| Q4 | **Situation, not trait** | membership never changes; nothing happened to them |
| Q5 | **Tension present** | only one signal, or two signals that do not pull against each other |
| Q6 | **Copy-safe opener exists** | the only way in is a funding round, layoff, departure, lawsuit, health or personal data |
| Q7 | **Addressable** | under ~30 companies (do it 1:1, by hand) or over ~50k (still a firmographic) |
| Q8 | **Fits the offer** | the pain is real but you do not sell the fix |

Q1, Q2, Q5 and Q8 kill. Q3, Q4, Q6 and Q7 send it back to be narrowed or reframed.

**Checkpoint.** Show the user the EDP, the surviving segments (situation, tension, evidence count,
membership test, public/proxy flags) and the open questions. **Wait for corrections.** Nothing paid runs
before this.

### Phase 5: Validate

Three checks turn a hypothesis into a measured segment. `references/validation.md` has the method.

1. **Count it.** Size each segment with a free or near-free count: AI Ark preview via
   `python3 skills/ai-ark/aiark.py preview --body b.json` (1 credit/page, read the total), Freckle
   `--preview` (free), job-board counts. Record the number, the query and the date. Count each
   condition on its own as well, to see which one does the narrowing.
2. **Audit five real rows by eye.** Pull 5 accounts that the test says are in, open the evidence, and
   check each one is really in the situation. Record the hit rate. Measured: 19 of 49 rows from one
   Exa run failed the "no system" condition when checked, and one rule-based fit list was 27% wrong
   on 100 accounts. **If 2 of 5 fail, the membership test is wrong. Fix it before counting further.**
3. **Backtest against your customers.** For your last 20-50 closed-won accounts, check what share
   were in this situation *in the 90 days before they bought*, then the same check on a random sample
   of your TAM. The ratio is the **lift**. A segment with lift under ~2x is a firmographic in
   disguise. No customer data available: use the seed accounts from the calls or replies and label
   the result `seed-check, not backtest`.

**Paid calls or more than 10 rows need the user's explicit OK, with the estimated cost shown first.**
Free lookups (counts, public pages, DNS, job pages) run without asking.

Mark each segment `measured` (all three done), `partly measured` (say which is missing) or
`hypothesis`.

### Phase 6: Build spec

For each measured segment, write what the team needs to build and refresh it without you:

- **Scoring**: points per condition, the threshold to fire, and the tie-breaker. Score known accounts
  with stacked signals, but **discover rows with one filter**: stacking discovery filters is what took
  one measured list from 50 rows to 2.
- **Build recipe**: the exact Clay table (columns in order, with the source of each), or the Exa Agent
  prompt plus schema, or the AI Ark filter JSON (run via `aiark.py` with `--out` into the play's
  `leads/` folder, and `--known <old csvs> --new-only` before any per-row paid step). Exa traps: target
  count in the prompt text, never `minItems`; always pass `schema=`; absolute dates; evidence links
  only, no enrichment fields.
- **Qualification Claygent**, when a condition needs judgment: inputs, the question, the allowed
  answers including `unknown`, and the rule that `unknown` never counts as a pass.
- **Half-life and refresh**: how long a row stays true (a job post: ~30-60 days; a filing: until the
  deadline) and how often to re-pull.
- **Exclusions**: your customers and open opportunities, competitors, partners' accounts, and anything
  the team has ruled out.

### Phase 7: Message

A PQS message names the situation and asks if the read is right. It hands over no gift; that is
pvp-builder's job.

- **Open on the situation, in the buyer's words** from the language bank. Borrow the vocabulary;
  **never quote a named prospect or customer to another prospect.**
- **Say what you saw and where**, with the field: "your BDR ad from 18 Aug, and nobody on LinkedIn
  running the team".
- **Ask whether the read is right**: one line they can answer without a meeting.
- Proxies are asked about, never asserted. Old evidence is labelled as possibly stale.
- Don't read them their own facts as if they were news (they know they are hiring). The value is the
  **implication** they have not put into words yet.

Then run one skeptical-buyer subagent per top-3 segment, as in pvp-builder phase 6: give it the persona
with the real objections from calls and replies, the message and the evidence, and ask *why would you
delete this, and what here is a leap?* A PQS breaks faster than a PVP because the inference is bigger.
Fix the inference or soften the claim, then attack once more.

### Phase 8: Ship

For each segment you will run, create the play folder and write
`plays/<play-slug>/research/pqs/YYYY-MM-DD-pqs.md` from `templates/pqs-doc.md`, plus
`plays/<play-slug>/research/pqs/YYYY-MM-DD-segments.csv` (one row per segment: name, situation,
conditions, count, hit rate, lift, status, refresh cadence). A company-wide run that ranks many
segments goes in `research/pqs/` at the repo root, with one play created per segment you pick. Then:

- Log each measured segment: `python3 gtm.py log-intel --play <play-slug> --category segment --label "..."
  --insight "count, hit rate, lift" --status observed`. Log segments the audit or backtest killed too,
  with `--status retired` and the reason in `--insight`, so nobody re-proposes them.
- Give the user a short recap in chat: the top 3, what was measured, what is still a hypothesis, and
  what is blocking.
- Offer the handoff: "Run `/pvp-builder` on this play to turn the top segments into gifts."
  pvp-builder phase 2 starts from this doc when it exists.
- Offer an HTML page or a doc if it is going to someone outside the outbound team.

---

## Rules that are not optional

- **READ-ONLY on your sending tools and CRM in this skill** (Instantly, Lemlist, the CRM, your
  database). Reading the CRM for closed-won is fine. This skill never creates a list in a CRM, loads a
  lead or launches a campaign.
- **A failed lookup is unknown, not a negative.** "No RevOps found" from one search is not "they have no
  RevOps". Measured once: counting HTTP failures as "no" turned 35 sending domains into 16.
- **Counts carry their query and date.** A number without both cannot be rebuilt.
- **No customer data in another prospect's segment or message.** Backtests stay in the build doc.
- **Your copy rules win.** Check `company/context.md` for banned words, dash rules and sign-offs.
  Default: no em or en dashes.

## Anti-patterns

- **The firmographic in costume.** "Fast-growing SaaS companies scaling their sales team" is industry +
  size + a vibe. Ask what happened to them, and when.
- **The one-signal segment.** "Companies hiring SDRs." Every sales vendor fires on it the same morning.
  Find the H2 that makes it hurt.
- **Stacked discovery filters.** Five conditions in one search returns two rows. Discover on one, score
  on the rest.
- **The unprovable core.** "Companies whose ZoomInfo contract renews next quarter." Renewal dates are not
  public. That is a question for the call, not a segment.
- **Segments from beliefs only.** "Our buyers are VPs of Ops at manufacturers" is what the team thinks.
  Check it against who actually bought.
- **Skipping the eyeball.** A list of 2,000 that is 40% wrong costs more than a list of 200 that was checked.
- **Counting the copy-unsafe signal as the segment.** Funding, layoffs and new-leader moves explain *why
  now*. They score; they never open.

## Files

| File | What it is |
|---|---|
| `references/segment-anatomy.md` | Situation, tension, amplifier, EDP, half-life, PQS vs PVP vs firmographic, in our words |
| `references/call-mining.md` | Extraction schema, the subagent prompt, batching, the language bank |
| `references/validation.md` | The 8 gates, counting, the 5-row audit, the customer backtest and lift, status labels |
| `templates/pqs-doc.md` | The phase 8 doc skeleton |
| `templates/segment-card.md` | One segment, fully specified |
| `../pvp-builder/references/data-sources.md` | Where pain shows up in data, measured costs and traps (shared) |
| `../pvp-builder/templates/context-pack.md` | Phase 0 skeleton (shared) |
