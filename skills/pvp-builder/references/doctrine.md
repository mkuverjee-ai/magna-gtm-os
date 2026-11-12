# Doctrine: the concepts, in our words

Jordan Crawford's framework, distilled in our own words. For his own words, run `/edge <concept>`
(licensed per person). Don't copy Edge text into this repo.

---

## Pain segment: the primitive

A pain segment is a group defined by a **situation the company is in**, not by what the company is.
"Mid-market SaaS in the US" is a firmographic, and everyone has that list, so you end up competing on
copy. "SaaS companies that posted a founding-SDR role in the last 30 days and have zero cold-sending
domains" is a pain segment, so you compete on data, and the message mostly writes itself.

How to tell you have one:
- It *happened to* them (a filing, a hire, a change, a deadline), rather than being something they *are*.
- Membership is a field in a database, not a box on a form.
- A ten-year-old could understand it in one sentence.
- It decays. A pain segment has a half-life and an ICP does not. Re-pull it on a schedule.

## Existential data point (EDP)

Pain comes in two kinds. **Incremental** pain is "this could be better": efficiency, nice-to-have,
competing with every other efficiency pitch. **Existential** pain is "if this stays broken, someone
loses their job, the company loses the contract, or the quarter misses". The EDP is the specific
number that puts a prospect in the second category.

Signs you've found it:
- If the number is true, it materially threatens revenue, compliance, or the reader's job.
- Stating it makes a reasonable executive uncomfortable.
- A CFO's reaction is "is this real?", not "so what?".

Most verticals have one EDP with a threshold, like fleet utilisation below ~70% or equipment
utilisation below ~60%. Mapping the EDP against a second axis (utilisation x margin) gives you 2-4
pain segments at once.

## PVP: permissionless value proposition

A message the buyer can **act on without replying**. It carries a complete, usable piece of
intelligence: the permit next door, the competitor's ad that has run for 200 days, the three reposts
of the same role. Nobody gave you permission to be in the inbox, so you don't ask for it. The value
lands first, and the reply is a side effect.

Tests:
- **Forward test:** could they forward it to a colleague and it still be useful? Then it's a PVP.
- **CTA-removal test:** delete the ask. Is anything of value left?
- **Pay test:** would they have paid a small amount to receive this, even if they never buy?

How to build one:
1. Start from a pain segment that passes the Texada test. A pretty message on a fake segment is a fake PVP.
2. Find where the pain leaves fingerprints: name the table, the field, the query.
3. Pull concrete rows: the actual company, record, date, amount. No rows means no PVP. Go back to
   the data, not the copy.
4. Compute the non-obvious piece. The raw fact they already know. The **synthesis** (the pattern across
   records, the clustering, the downstream consequence) is the gift.
5. Wrap it in PEA or POM. Short. Every sentence is a fact or the implication of one.
6. Adversarial review, fix, then ship.

**When not to use it:** when the data is thin and the "synthesis" is a guess (a thin PVP is worse than
an honest PQS); when high-volume, low-ACV economics can't carry the research; in warm channels
(follow-ups, referrals, replies).

## PQS: pain-qualified segment

The honest sibling for when the evidence proves a pain is likely but doesn't hand over something
the buyer can act on alone. It usually triangulates 2-3 weaker signals (reposted jobs + funding +
new head of talent) into a pattern, ranks accounts by how cleanly the signals hit, and asks an
invitational question: *"here's what I see, here's where it's from, am I reading it right?"*

Use it for data-thin industries and softer pain (growth tension, process change). Don't use it when
the data would support a PVP (don't soften unnecessarily), or when the "pattern" is two weak signals
you hope correlate. A skeptic pokes holes in a PQS faster than a PVP because the inferential leap is
bigger.

## Texada test: the specificity gate

Three gates. Fail any one and it's a hunch, not a segment.

1. **Hyper-specific:** dates, counts, record numbers, addresses, field values. Not "recent", "many",
   "growing". If it couldn't go in a spreadsheet row with the source column filled, it fails.
2. **Factually grounded:** every claim answers "which field, from which database?" without improvising.
   No "likely", "probably", "in our experience".
3. **Non-obvious synthesis:** the buyer doesn't already have this. "You got an OSHA citation" fails
   (they know). "Your six open citations cluster into three deadlines inside 120 days" passes.

It takes about three minutes per segment. The segments it kills would otherwise die slowly in
production, after the sends had already gone out.

## Generalities breed skepticism

If you could swap the company name for any other and the sentence still works, it's a template, and
the reader's default (correct) response is to delete it. One record number, address, or date changes
their question to "how do they know that?", and that question keeps them reading. When you can't write
the specific version, the research isn't finished. Don't cover the gap with adjectives.

## PEA: Preview, Engage, Ask

- **Preview:** the first ~120 characters (what a phone shows). One concrete, recognisable, verifiable thing.
- **Engage:** prove the work. Specific fields and numbers.
- **Ask:** one low-friction request that takes one breath to answer. No calendar links.

## POM: Subject, Intro, Insight, Inquisition

The four-part variant: a 2-4 word curiosity subject, an intro that states the exact situation with the
database's own IDs and dates, an insight with the non-obvious consequence, and a one-line "did I get
that right?" question. Use PEA for mobile-first and short, POM when the specificity has to carry the
whole email.

## Adversarial buyer

Every sender thinks the draft is good, and every buyer thinks most email is spam. The buyer wins. So
give a model the persona **with the real objections the team has heard** and ask it why it would
ignore the message, not whether the message is good. Critique, rewrite, critique again. This shrinks
a six-week reply-rate feedback loop to five minutes, and it kills copy that only sounded good in the
meeting.

## The list is the message

If the segment is right, you barely have to write. If you're struggling to write, go back to the
list. Targeting *is* messaging.
