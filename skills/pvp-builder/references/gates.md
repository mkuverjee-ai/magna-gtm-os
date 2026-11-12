# The gates (G1-G8 for every gift, G9-G11 for everything)

Score every candidate. Each gate gets **PASS / FAIL + one-line reason**. No partial credit, no "mostly".

| # | Gate | Kill or demote on fail |
|---|---|---|
| G1 | Hyper-specific | **KILL** |
| G2 | Factually grounded | **KILL** |
| G3 | Non-obvious synthesis | demote to PQS / back to phase 3 |
| G4 | Independently useful | demote to PQS |
| G5 | Existential, not incremental | demote (keep only if everything else is strong) |
| G6 | Legitimate | **KILL** |
| G7 | Deliverable at scale | **KILL** (or re-gate the segment to match capacity) |
| G8 | Bridges to the paid offer | back to phase 4 (redesign the ask) |
| G9 | Incumbent test | back to phase 4 (it sells for the incumbent) |
| G10 | Belief test | **KILL** as a hook (may survive as a post-yes asset) |
| G11 | 10-second yes | redesign the ask |

Offers that are not information (risk reversal, a service slice, access) skip G1-G3 but must pass
G6, G7, G8 and G9-G11, and must name the **internal commitment** they need (money, data, people, a written rule).

---

## G1: Hyper-specific
- FAIL: "Your competitors are running a lot of ads right now."
- PASS: "<Competitor> has run the same UGC video since 2026-03-02 (207 days) with 14 live variants."

## G2: Factually grounded
Every claim on the card has a `source.field` next to it. "Estimated", "typical", and "industry average"
fail unless the estimate's method and source are written down.
- FAIL: "Brands like you usually lose 20% of carts to shipping anxiety."
- PASS: "Your checkout loads 3 third-party scripts before the shipping estimate (BuiltWith, fetched 2026-09-25)."

## G3: Non-obvious synthesis
Would a mid-level analyst at the prospect already know this? Then it fails.
- FAIL: "You're hiring 4 SDRs." (They wrote the job post.)
- PASS: "You're hiring 4 SDRs and your 2 existing sending domains have no DMARC, so the new hires will
  send from infrastructure that is already hurting deliverability."

## G4: Independently useful
Delete the CTA and the sender's name. Forward it to someone in the same role at another company.
Could they act on it? If not, it's a pitch.

## G5: Existential, not incremental
Tie it to the EDP. Does it threaten revenue, compliance, or the reader's job? "Save 5 hours a week"
is incremental. "Your largest payer's new rate schedule hits 412 of your patients in 60 days" is
existential.

## G6: Legitimate
All must be true:
- [ ] No invented numbers, customers, logos, or benchmarks. Proof points come from the approved list
      in `company/context.md` (via the context pack), quoted and sourced.
- [ ] No single-customer data from your product. Aggregates only, with a minimum cohort size
      (default n>=10) and nothing identifying.
- [ ] Data was obtained lawfully and within the source's terms (public records, ad libraries, public
      pages, licensed providers). No scraped private data, no personal/health/financial data about
      individuals.
- [ ] No regulated claims you can't make (financial returns, medical outcomes, legal advice).
- [ ] No false urgency. A deadline in the copy is a real deadline from a real source.
- [ ] Not creepy. Company-level operational facts are fine. Personal life, individual surveillance,
      and exact departure/layoff names are not.
- [ ] The offer the email names actually exists (or will exist by the time of send, with an owner and date).

## G7: Deliverable at scale
Fill in: **unit cost / prospect**, **time / prospect**, **who produces it** (tool, service, or person),
**capacity per week**, and **segment size**. If segment size is greater than capacity x campaign
weeks, gate the segment tighter (tier, ad count, revenue) until it fits, or pick a different delivery
mode. Check the unit cost against ACV. Rule of thumb: research cost per prospect should be under ~0.5%
of first-year ACV x expected reply-to-deal rate. Say the math out loud on the card.

## G8: Bridges to the paid offer
The gift should be a free slice of what you sell, so that "want us to do the rest?" is the
obvious next step. A useful gift that's unrelated to the offer creates goodwill and no pipeline.
- Weak bridge: a customer-voice report sent by a Meta ads agency, with no hooks attached.
- Strong bridge: the same report plus 10 ad hooks built from the customers' exact words, where the
  agency makes 10-15 ads a month.

## G9: Incumbent test
Two questions: could the buyer's **current vendor** send this same thing tomorrow? And does this gift, read
on its own, push the buyer toward that vendor? Either yes fails.
- FAIL (measured): "61% of <incumbent>'s stores cover lost parcels at checkout, about half with
  <incumbent>'s own option." Both skeptical reviewers said they'd forward it to their <incumbent> account
  manager.
- PASS: something only you can do or know: a network aggregate of your own claims data, a guarantee the
  incumbent doesn't offer, a capability the incumbent lacks (verified on the incumbent's own public pages,
  not only your own comparison doc).

## G10: Belief test
Would a stranger believe this sender can produce this, from the outside, without the buyer's data?
- FAIL: "I can give you a profit forecast" in a cold email. The buyer's reaction: "You really can't. How
  could you possibly put one together?" Keep it as an asset for after a yes.
- PASS: a mockup of their own checkout, a list built from a public registry, a remake of their public ads.
  The buyer can see how it was made.

## G11: 10-second yes
Can the buyer answer the ask in one breath, without looking anything up and without revealing anything
private? "What's your revenue share?" fails (they won't tell a stranger). "Want the file?" passes.

---

## Ranking survivors

```
score = (value_to_buyer 1-5) x (bridge_strength 1-5) x (confidence 1-5) / cost_band
cost_band: 1 = <$0.10/prospect, 2 = <$1, 3 = <$10, 4 = >=$10
confidence: 5 = sample-verified on a real prospect, 3 = data recipe tested with a count, 1 = hypothesis
```

The formula is a tiebreaker, not an oracle. Write one sentence per survivor on *why it ranks where it
does*.
