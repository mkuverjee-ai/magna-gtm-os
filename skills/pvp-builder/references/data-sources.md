# Where pain leaves fingerprints

Use the sources this repo is set up for (see `TECH-STACK.md` and `python3 gtm.py keys` for which keys
you have), plus free public records you can read on the open web. AI Ark is the primary source for
companies, people and emails; Exa, Ocean, Apify, Freckle and the Clay CLI are optional. Costs are
**measured** where marked; everything else says "verify".

**If a recipe only works with a tool you have no key for, say so and let the user decide.** Don't
quietly substitute another provider.

**Sending tools and the CRM are READ-ONLY in this skill** (Instantly, Lemlist, the CRM). Reading your
CRM or campaign stats for "why did customers buy" or "what got replies" is fine. Writing is never part
of this skill.

---

## Check what you already have (free, always first)

| Source | Use | Notes |
|---|---|---|
| `plays/*/leads/` CSVs (and each play's `leads/REGISTER.md`) | Every list you already pulled and paid for | Check a known list of domains here before any paid pull; pass old CSVs to `aiark.py --known` |
| `python3 gtm.py intel [--play <slug>]` | What worked and what didn't | Read before proposing an offer; don't re-propose what already failed |
| `python3 gtm.py meetings` / `gtm.py transcript --date ...` | Call transcripts in your own database, if you record calls | The source for the language bank and buying moments |
| Instantly / Lemlist reply bodies (read-only) | Buyer language, what got a yes | Often the richest source when calls are sparse |

## Sizing (count before you design)

| Source | Use | Notes |
|---|---|---|
| AI Ark via `icp-tam-mapper` / `skills/ai-ark/aiark.py` | Company and people TAM -> SAM -> SOM | Preview first (1 credit/page); previews mask names and carry no emails. Use `latest` title, not `current` (current includes side gigs). 10k-row cap per query: slice by country x headcount and sum |
| Freckle `--preview` | Counts on a known set | Free and exact. Freckle cannot source a list |
| Your past pulls in `plays/*/leads/` | Overlap with what you already own | Free |

## Finding the rows

| Source | Good for | Notes |
|---|---|---|
| AI Ark (`aiark.py`) | Companies and people by firmographics, titles, tech, lookalike domains | Always via `aiark.py`, with `--out` into the play's `leads/` folder so the team has the record. `--known <old csvs> --new-only` before any per-row paid step |
| Exa (`exa-search`, Exa Agent) | Situations that only show on the web: job posts, filings, announcements, case studies, posts | Measured on a 49-row job-post run: ~0.39 USD per row returned. Put the target count in the prompt text, **never `minItems`**; always pass `schema=`; absolute dates; ask for evidence links, not enrichment fields |
| Ocean.io (`ocean-lookalike`) | Companies like a customer or a competitor's customer | 0.2 credits each, count first |
| Google Maps via Apify (`google-maps-scraper`) | Local businesses | ~0.00275 USD/place (measured). `--max-usd` required. Sourcing only |
| LinkedIn via Apify (`linkedin-scraper`) | Who engaged with a post, recent posts | ~0.007-0.011 USD/profile/day (measured). Sourcing only |
| Clay CLI (`clay-cli`) | Running a Clay table or workflow | A green run proves nothing; check the output |

## Enriching a known record

| Source | Use |
|---|---|
| AI Ark (`ai-ark` skill) | Emails, LinkedIn, firmographics on records you already have. Verify emails before anyone is mailed |
| Freckle, Clay CLI | Research and scoring columns on a known list |

## Free public records (read on the open web; cite the URL and date)

| Source | Pain it proves |
|---|---|
| Company websites, careers pages, case studies, pricing pages | Stack named in job ads, roles being hired, proof, prices |
| Shopify storefronts: `/products.json`, `/policies/*` | Catalogue and price points, stated returns/shipping policy |
| Vendor documentation and lifecycle pages (e.g. Microsoft Learn) | Real end-of-support and removal dates |
| Company registries (Companies House, state SoS, EU registers) | Entities, filing dates, year-ends, acquisitions |
| SEC EDGAR (10-K, 8-K) | Stated targets, risk factors, site counts |
| Building permits, OSHA/EPA/FDA inspection data, court dockets, USAspending/SAM.gov, licensing rosters | Regulated, dated events with record numbers |
| DNS / page source (scripts, widgets, MX, SPF, DMARC) | What a site actually runs. **Presence is proof, absence is not** (widgets inject at runtime) |

## Your own data (ask for it, read-only)

The context pack should list what the company can export: CRM closed-won/lost with dates and reasons, product
usage aggregates, assessment/quiz responses, support tickets, claims or transaction data, past campaign
performance. This is where "data only you have" offers come from. Aggregates only (n>=10), nothing
identifying, and legal sign-off before anything leaves the building.

## Known traps (measured)

- **A failed lookup is UNKNOWN, not a negative.** An HTTP failure once turned 35 sending domains into 16.
- **Shared widget names lie.** Three competing checkout vendors all called their widget "Checkout+"; an agent
  read the label as one vendor and marked ~150 of a competitor's stores as its customers. Match on the vendor's
  own script domain.
- **Site counts from data vendors** can be 4x too high (they count tenant spaces) or too low (they miss
  locations). Use them to rank, never to state.
- **Rule-based fit labels misfire.** One list was 27% wrong on 100 accounts checked by hand (franchises,
  carmakers, banks). Audit five rows by eye before trusting any list.
- **A comparison doc is a claim.** Verify every competitor fact on the competitor's own public pages
  before it goes in copy (one matrix had out-of-date competitor pricing and overstated a coverage gap).
- **Stacking discovery filters kills volume.** One filter: 50 rows. Add "started in the last 30 days": 2 rows.
  Discover on one condition, score on the rest.
