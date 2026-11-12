---
name: pvp-builder
description: >
  Build legitimate offers for your own outbound from every piece of context you can feed it:
  company/context.md (ICP, positioning, proof, personas, offers), call transcripts if you record
  calls, campaign replies, case studies, customer lists, product data, your website. Goes wide first
  (10 lenses: information gifts / PVPs, mockups of the prospect's own thing, risk reversal like a free
  first month or contract buyout, done-for-you slices, data only you have, incumbent killers, timing),
  then narrows to ranked, gated offer stacks you can actually deliver (named data source, unit cost,
  internal commitment, sample email, bridge to the paid offer), with one proven on a real prospect.
  Use when someone says "build offers", "what PVPs could we run", "what can we give away", "lead
  magnet ideas", "is this a real PVP", "we need a stronger offer", or drops a pile of context and asks
  what to send.
---

# PVP Builder: offers you can actually deliver

This skill takes everything you know about your company, your buyers and a play's segment, and
turns it into **permissionless value propositions your buyers would pay to receive**: gifts you can
produce repeatedly, from data that exists, at a known cost, that bridge to what you sell.

Work happens per **play**: `plays/<play-slug>/` with `research/`, `leads/companies/`,
`leads/contacts/`, `campaigns/` and `reports/`. Company-wide context (ICP, positioning, proof,
personas, offers) is in `company/context.md`.

Run `skills/pqs-builder` first when you have calls, replies or customer data; this skill picks up its
segments. The theory is Jordan Crawford's; `references/doctrine.md` is a distillation in our own
words. If you have your own Edge Copilot license (per person), `/edge` can pull the source entries
`pvp`, `pvp-methodology`, `texada-test`, `existential-data-point`, `pqs-methodology`, `pea`, `pom`,
`adversarial-buyer`. **Never paste Edge content into files in this repo.** It is licensed per person
and fingerprinted.

## The sentences everything hangs off

1. **A PVP is a message the buyer can act on without ever replying.** Remove the CTA. If it is still
   worth forwarding to a colleague, it is a PVP. If not, it is a pitch in costume.
2. **The list is the message.** A PVP is built on a *pain segment*, a situation that happened to the
   company and left fingerprints in a database. It is not built on a firmographic. If the copy is hard
   to write, the segment is wrong.
3. **Legitimate means deliverable and true.** Every claim traces to a named source and field, you can
   produce it for the 500th prospect as well as the first, and nothing in it was invented, leaked, or
   implied.
4. **A gift earns attention; an offer earns the yes.** An information gift (the classic PVP) is one cell of
   a bigger space: building their thing, taking a job off them, removing the risk of switching, access to
   data only you have. Go wide across that space before narrowing. Measured on one programme: two rounds
   of information gifts sent buyers to their incumbent or read as unbelievable; the ideas that moved it
   were a risk-free switch, a mockup of the buyer's own checkout and a free claims desk for peak season.

---

## Workflow

Run the phases in order. Each one has a **reject state**. When a phase fails, go back; do not paper
over it in the copy.

```
0 INTAKE        gather + tag every source             -> context pack
1 ASSETS        what can you uniquely produce?          -> asset inventory
2 PAIN          situations, existential data points      -> pain segments
3 FINGERPRINTS  where does each pain show up in data?    -> data recipes
4 DIVERGE       10 lens subagents -> 40+ raw ideas, NO gates     -> long list
   CHECKPOINT   user picks what's worth exploring (incl. the odd ones)
4b CONVERGE     cluster, combine into stacks (gift + offer + next step) -> 8-15 candidates
5 GATE          G1-G8 + incumbent (G9) + belief (G10) + 10-second yes (G11)
6 ATTACK        buyer subagent: critique AND "what would you say yes to?" -> rewrite
7 PROVE ONE     run the recipe on ONE real prospect       -> sample-verified card
8 SHIP          offer doc in the play folder + intel logged + recap
```

### Phase 0: Intake. Build the context pack

Pull **everything** the user points at, then look for more before asking. Search order:

- `company/context.md` (`python3 gtm.py company` prints it plus which keys are set). If a section is
  marked as a draft or unverified, say so and treat it as unverified.
- The play's folder, if one exists: `plays/<play-slug>/research/` (a `/pqs-builder` doc in
  `research/pqs/` especially), `campaigns/`, `reports/`. Other plays' `reports/` for what already ran.
- `python3 gtm.py intel` (what already worked or failed: never re-propose a disproven offer)
- **Calls, if you record them:** `python3 gtm.py meetings [--limit N]`, then
  `python3 gtm.py transcript --date YYYY-MM-DD` for each one you need. Anything missing from your
  database: the `fireflies-mcp` skill. Recordings may be confidential; pull only what you need.
- **Your own campaign results, read-only** (keys via `gtm.cred("INSTANTLY_API_KEY")` /
  `gtm.cred("LEMLIST_API_KEY")`): analytics per campaign and the actual reply bodies. Real replies are
  the best buyer language you have, and "what got a yes" is the strongest evidence of an offer that
  works (one measured programme: ~9,500 sends, 1 positive, and that one asked for a profit forecast).
  Reading is fine; never create, load or send.
- Your own competitor comparison docs: verify every competitor claim on the **competitor's own public
  pages** before it goes in copy (comparison matrices go stale, especially on pricing).
- Your website: home, product, pricing, customers/case studies, about, careers
- Anything the user pastes or drops in

**No transcripts?** Recordings are often sparse or confidential. The skill still works from
`company/context.md`, the customer list, win-loss notes and campaign replies. Say in the pack which
of these you had, and mark buyer-motivation lines `[team belief]` until a reply, a win or a backtest
backs them.

Write the pack to `plays/<play-slug>/research/pvp/context-pack.md` (or `research/pvp/context-pack.md`
at the repo root for a company-wide run) using `templates/context-pack.md`. **Every line carries a
source tag** (`[call 2026-09-08 34:10]`, `[site /pricing, fetched 2026-09-25]`,
`[company/context.md §proof]`, `[reply 2026-09-12, campaign X]`). Mark a line `[ASSUMPTION]` when it
has no source.

**Hard rule:** never write positioning, proof points, prices, or customer names from background
knowledge. Source it or leave a `[SLOT: ...]`. A confident line from memory reads exactly like a wrong
one until someone checks.

The pack must answer these questions. The gaps become questions for the user at the end of phase 2,
never guesses:

| Question | Why it matters |
|---|---|
| What do we sell, to whom, at what ACV? | ACV decides how much research per prospect is affordable |
| Who is the buyer, and what gets that person fired or promoted? | The existential data point lives here |
| Why did our best customers buy, *at the moment they bought*? | Pain segments come from real wins, not ideas |
| What proprietary data or capability do we have? | The strongest PVPs are made from what only you have |
| What can we deliver on a yes, and how fast? | A gift you cannot produce is a lie with a delay |
| What proof may be used publicly? What is confidential? | Legitimacy gate |
| What have we already tried in outbound, and what happened? | Do not re-propose what failed |

### Phase 1: Asset inventory. What can only you hand over?

This is the difference between a real PVP and a generic "free audit". List what you have, in four
buckets (`references/archetypes.md` has the full catalogue with examples):

1. **Proprietary data exhaust.** Aggregates across your customers or your product's traffic: benchmarks,
   rate tables, performance distributions ("median utilisation across 400 fleets"). Always anonymised
   and aggregated, never one customer's data.
2. **Expert capability.** Something your team can produce for a prospect in under an hour with the
   tools you already have: a teardown, a remake, an audit, a model. A paid-ads agency remaking
   competitors' top 5 ads with the prospect's logo is this bucket.
3. **Vantage point.** What you can see because of where you sit in the market: who is switching,
   which regulation is biting, what the buyer's own customers say.
4. **Public data only you know how to read.** Permits, filings, ad libraries, job posts, DNS, reviews.
   The data is free to everyone; knowing which field matters is your expertise.

Reject state: if all four buckets are empty, the best PVP is a public-data synthesis (bucket 4, done
by research rather than proprietary data). Say so plainly. It is still viable, but it is a weaker moat.

### Phase 2: Pain segments and the existential data point

**If `plays/<play-slug>/research/pqs/` (or `research/pqs/`) holds a `/pqs-builder` doc, start from it.**
Take its measured segments as the pain segments, skip the drafting below, and carry their counts,
audits and language bank forward. If it does not exist and you have more than ~15 calls, a body of
replies, or customer data to backtest, run `/pqs-builder` first; the steps below are the light version
for when it hasn't been run.

For the buyer, find the **existential data point (EDP)**: the one number that, when it moves past a
threshold, costs someone their job, the company a contract, or the quarter its target. It is not an
efficiency gain; that is incremental pain, and incremental pain has to be *sold*. Examples of the
shape: fleet utilisation under 70%, a payer cutting reimbursement 14% in 60 days, a job reposted
three times in a quarter, a sending domain with no DMARC before the first SDR starts.

Then build **pain segments**: groups defined by a situation that *happened to* the company, which
changes over time, and whose membership is a field in a database.

- Start from your real customers (phase 0 table): what was true at the moment they bought?
- Find the **tension**: two facts pulling against each other (hiring an SDR + no sending estate;
  new product launch + ads still on old targeting). One signal is noise, and the pull is the pain.
- Add the **amplifier**: a deadline, a target, a season, a regulation date.
- Size it. One count per segment, from a free or cheap count endpoint (`references/data-sources.md`).
  Under ~300 accounts is a 1:1 play; over ~50k usually means the segment is still a firmographic.

**Don't stack signals to find rows.** Measured: one filter gave 50 people, and adding a "started in the
last 30 days" condition dropped it to 2. Stack signals to *score* known accounts, never to *discover*
them.

**Checkpoint with the user here.** Show the EDP, 3-6 pain segments with counts, and the open questions
from phase 0. Wait for corrections before generating. A wrong segment wastes every phase after it.

### Phase 3: Fingerprints. Where each pain shows up in data

For each segment, write the **data recipe**: source, then field, then query, then what a row looks like.
If you cannot name the field, you do not have a PVP yet. `references/data-sources.md` lists what you
can reach from this repo, with measured costs and traps.

```
Segment:  SaaS 50-500 emp, hiring first SDR, no cold-sending domains
Source 1: job postings (Exa / Clay)        field: title ~ "SDR|BDR", posted_at <= 30d
Source 2: DNS lookup on lookalike domains  field: outbound_domain_count == 0
Row:      acme.io | "Founding SDR" posted 2026-09-14 | 0 outbound domains | DMARC p=none
```

Reject state: a query that returns no concrete rows sends you back to the data source, never on to
the message.

### Phase 4: Diverge. Go wide before going narrow

Read `references/offer-space.md` first. The goal here is **range and quantity**, not quality. Gates come later;
applied now, they kill the odd idea before it can turn into the good one.

Spawn **one general-purpose subagent per lens, in parallel** (the 10 lenses are in `offer-space.md`:
information gift, build their thing, risk reversal, done-for-you slice, data only you have, incumbent
killer, timing, borrowed from the offer library, the buyer's 10-second yes, unlimited budget then shrink).
Give each: the context pack, the segment(s), the asset inventory, your competitors, real buyer objections
from calls and replies, and the offer library. Ask for **5+ ideas each, one line each plus "what it would
take"** (data, build, internal commitment, cost). No self-censoring.

Merge into one **long list of 40+**, de-duplicated, each tagged with its grid row (information / artifact /
service slice / risk reversal / access / timing). **Reject state:** fewer than four grid rows covered means
you have not diverged; run the missing lenses again.

**Checkpoint with the user.** Show the long list grouped by grid row, with your top 5 marked and a one-line
reason. Let the user pick, including ideas you would have dropped. They often know a commitment the
company can make that you don't (e.g. "we'd fund a buyout").

### Phase 4b: Converge. Stacks, then cards

- **Cluster** near-duplicates and keep the sharpest version.
- **Combine into stacks**: one thing that earns attention (gift or artifact), one thing that removes the risk
  of saying yes (offer), one obvious next step. A stack usually beats its best single part.
- Write **8-15 candidates** on `templates/offer-card.md`. For each segment where the evidence is a pattern
  rather than a proof, also write a **PQS fallback** (invitational: "here's what I see, am I reading it right?").

The fields that make a card legitimate are required, not optional: **source+field for every claim, unit cost,
build owner, delivery mode, bridge, and the internal commitment it needs**. "No field, no PVP" applies to every
*claim* inside a gift; an *offer* (a guarantee, a free service slice) needs an internal commitment instead
(budget, people, a written rule signed off by whoever owns it).

**Delivery mode** is a design choice, so state it:
- **In the email.** The insight or artifact itself is in message 1 (strongest, needs per-row data at send time).
- **Named in the email, delivered on yes.** "I pulled your competitors' 5 longest-running ads and
  remade them with your logo. Want them?" This only counts as permissionless if the thing already
  exists when you send it. "I could build you..." is a pitch.
- **Self-serve.** A page or tool the prospect runs. Good for data the prospect has to supply
  (call transcripts, their own CSV).

### Phase 5: Gate

Score every candidate with `references/gates.md`. Each gate is pass/fail with a reason:

| # | Gate | Fails when |
|---|---|---|
| G1 | **Hyper-specific** | "recent", "many", "growing"; no date/count/name/record |
| G2 | **Factually grounded** | any claim you can't trace to source+field |
| G3 | **Non-obvious synthesis** | the buyer already knows it ("you raised a Series B") |
| G4 | **Independently useful** | remove the CTA and it's worthless; not forwardable |
| G5 | **Existential, not incremental** | a CFO says "so what?" instead of "is this real?" |
| G6 | **Legitimate** | invented number, leaked customer data, private/creepy data, regulated claim, fake urgency |
| G7 | **Deliverable at scale** | you can't produce it for prospect #500 at the stated cost and time |
| G8 | **Bridges to the paid offer** | the gift is useful but leads nowhere you sell |
| G9 | **Incumbent test** | their current vendor could send it tomorrow, or it points the buyer at that vendor |
| G10 | **Belief test** | a stranger wouldn't believe we can produce it cold (a cold "profit forecast") |
| G11 | **10-second yes** | the ask needs thought, a lookup, or private numbers ("what's your rev share?") |

G1-G3 are the Texada test. Offers that aren't information (risk reversal, service slice, access) skip G1-G3
but must pass the rest. **Any fail on G1, G2, G6, G7 or G10 kills the candidate** (a G10 fail can live on as a
post-yes asset). A fail on G3, G4, or G5 demotes it to PQS or sends it back for more synthesis. Then rank
survivors on **value to buyer x fit to your offer / unit cost**, and note ACV: a 2k USD ACV can't carry
20 USD/prospect of research.

### Phase 6: Attack

Spawn an adversarial-buyer subagent (general-purpose) per top-5 candidate, in parallel. Give it the
buyer persona **with the real objections from calls and replies**, the sample email, and the data recipe.
Tell it to be a jaded, skeptical version of that buyer and answer: *why would you delete this? what
here is false or unverifiable? does it push you toward your current vendor? what would make you forward it?*
And then make it **generate**: *what would you say yes to in 10 seconds? what would you actually pay for?*
Feed those answers back into the candidates; in one measured run the best idea (a free 50/50 checkout
test the vendor runs for the buyer) came from this question. It's allowed to be harsh; that's the point.
Rewrite, then re-attack once. Drop anything that doesn't survive two rounds.

### Phase 7: Prove one

Take the #1 candidate and run the recipe on **one real prospect** from your TAM. That's one perfect
message to one perfect account, built by hand. If you can't make that one good, the segment is wrong,
and automating it only spreads the problem faster.

- Free lookups (counts, DNS, public pages, ad libraries) run without asking.
- **Any paid call, or more than 10 rows, needs the user's explicit OK first**, with the estimated cost shown.
- Mark the card `sample-verified: <prospect>, <date>`. Every other card stays `hypothesis`.
- **READ-ONLY on your sending tools and CRM in this skill** (Instantly, Lemlist, the CRM, your
  database). This skill never creates a campaign, loads a lead, or writes to a CRM.

### Phase 8: Ship

Write `plays/<play-slug>/campaigns/YYYY-MM-DD-pvp-offers.md`:

1. One-paragraph summary: the EDP, the winning PVP, and why.
2. A ranked table of survivors: name, segment + count, delivery mode, unit cost, gate score, status.
3. Full offer cards for survivors (the sample-verified one first).
4. Killed candidates with the gate that killed them. One line each; this stops the next person
   re-proposing them.
5. **Internal asks**, one per top offer: what it needs the company to commit (money to underwrite a
   guarantee, a data export, people, a written rule) and why it's worth it. The strongest offers usually
   need one. Plus open questions (missing proof, data access, confidentiality calls).
6. The long list from phase 4, grouped by grid row, so the next run starts wider.
7. Sources: the context pack path and every file/call/URL used.

Offer to build it as an HTML page or a Word doc if it's going to someone outside the outbound team.
**Log what you learned so the next play starts from it:** one
`python3 gtm.py log-intel --play <play-slug> --category offer --label "..." --insight "..." --status observed`
per surviving offer, and one with `--status retired` for any offer that your own results or the
skeptical buyers killed, with the reason in `--insight`. Then give the user a short recap in chat: the top 3, the one proven,
and what's blocking the rest.

---

## Message shape (for the sample email on each card)

PEA, ~75-90 words, plain text:

- **Preview (first ~120 chars):** one concrete, verifiable thing they recognise instantly. No
  greeting fluff, no "I", no company intro.
- **Engage:** the evidence and the synthesis. Specific fields, numbers, names. Every sentence delivers
  a fact or the implication of a fact.
- **Ask:** the smallest possible yes. "Want the list?" / "Am I reading that right?" / "Want them?"
  Never a calendar link, never "15 minutes", never a meeting in message 1.

Subject line: 2-4 words, earns curiosity rather than understanding (`5 ads you're missing`,
`Permit #48213`). For uncomfortable insights, use the anti-threat frame: put the bad outcome in
*other* companies' past, and make the reader the hero.

**Write in the buyer's vocabulary, not ours.** Before drafting, pull a language bank from calls and replies for this
segment: the exact phrases prospects used for the pain ("a list of 100 target accounts", "no way to rank or structure
their time"). Put a table in the offer doc (phrase, who, where it's used), echo the vocabulary in the copy, and **never
quote a named prospect** to another prospect. Run the mirrored version as an A/B against the plain one. Our own
words ("ICP", "signal", "PVP") belong in the build doc, not the email.

Your copy rules override defaults. Check `company/context.md` for banned words, dash rules and sign-off
conventions. Default: **no em or en dashes**.

---

## Anti-patterns (the reasons PVPs die)

- **Value-ish.** "We put together some insights on your market, want to see them?" with nothing
  specific named. Name the thing and one number from it, or it is a pitch.
- **Describe instead of deliver.** "I could build you a report" is an offer to do work. The PVP is
  the finished work.
- **Data dump.** 40 rows pasted in with no synthesis. The synthesis is the product, not the rows.
- **One customer's data in another's inbox.** Proprietary-data PVPs are aggregates with a minimum
  cohort size (default n>=10) and no identifying detail. Never identifiable; start with past or
  inactive customers.
- **Invented benchmarks.** "Companies like yours see 2-3x reply rates" with no source. Delete it or
  cite it.
- **Copy-unsafe signals as openers.** Funding rounds, layoffs, departures, lawsuits, and health/personal
  data explain *why* an account matters. They are never the opener.
- **Gifts you can't fulfil.** A remade-ads offer to 2,000 prospects when the design team can do 10 a
  week. Gate prospects so volume matches capacity (e.g. top tier only, 50+ active ads).
- **Reading them their own facts.** Their filing dates, their ERPs, their acquisitions, a partner's own customer list: they
  already know, so it fails G3 and reads as surveillance. Hand over **outside** information (named peers, accounts outside
  their book, an option comparison). Measured on one programme: every "about you" draft failed round 1, and every
  "outside you" rewrite passed or became forwardable in round 2.
- **The scariest date instead of the true one.** Quote the full lifecycle (e.g. MDS on SQL 2022: mainstream to 2028,
  extended to 2033). Buyers check, and a cherry-picked cliff kills trust in everything else.
- **Threatening what they're protecting.** "This role can be automated" endangers a manager's headcount; "we'll sell into
  these accounts" endangers a partner's channel. Frame the gift as protecting both, and put channel rules in writing.
- **Gating the gift behind "want it?"** when it already exists. Attach it; ask a question they can answer in one line.
- **Only information gifts.** If every candidate is a report, a benchmark or a list, you skipped phase 4.
  Check the grid rows.
- **Pointing them at the incumbent.** "Here's how your peers solved it" sells whatever their current vendor
  already offers. Run G9.
- **The cold forecast.** A profit forecast from a stranger isn't believable. It's a post-yes asset (G10).
- **Horizontal mush.** "Everyone who sends email" isn't a segment. Keep narrowing until the membership
  test is one database field.

---

## Files

| File | What it is |
|---|---|
| `references/doctrine.md` | PVP / PQS / EDP / Texada / PEA / POM / adversarial buyer, in our words, with the "when not to use" for each |
| `references/archetypes.md` | Gift archetype catalogue by asset bucket, each with an example of the shape |
| `references/data-sources.md` | Where pain leaves fingerprints, what you can reach from this repo, measured costs and traps |
| `references/gates.md` | The 11 gates with pass/fail examples and the ranking formula |
| `references/offer-space.md` | **Phase 4.** The grid (what you give x when), the 10 lenses, the offer library, traps |
| `templates/context-pack.md` | Phase 0 output skeleton |
| `templates/offer-card.md` | One PVP spec card |
