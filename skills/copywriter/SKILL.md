---
name: copywriter
description: Write cold-email sequences that hold up to standards proven across hundreds of campaigns. Trigger when writing or rewriting cold outbound copy for a play, building a 2 to 3 step email sequence, or turning a strategy into launch-ready copy. Enforces length, structure, and craft rules and pulls angles from the campaign corpus.
---

# Copywriter

This skill writes cold email copy that holds up. It carries the rules to hold on every campaign and the patterns learned from the ones that worked and the ones that did not. Use it to write a sequence from scratch or to rewrite a draft that is not landing.

## Before you write

1. **Load the context.** Read `company/context.md` for positioning and proof, then the play's folder in `plays/<play-slug>/` (segment, ICP, research, any call notes). The copy is only as good as the context behind it.
2. **Know the angle.** What is the one reason this prospect should care right now? If you cannot say it in a sentence, stop and find it before writing.
3. **Know the audience's English.** Non-native or non-technical audiences get simpler language. Say it plainly, short words, no idioms.

## The rules (hard, non-negotiable)

- **Length.** Each email 75 to 90 words. Every sentence under 20 words.
- **No em dashes.** Rewrite to flow without them. Commas and periods carry the load.
- **Sequence shape.** Two or three steps only. Never four or five. If you cannot make your case in two or three emails, the offer or the targeting is the problem, not the copy length.
- **One ask per email.** No stacked CTAs.
- **Lead with the pain or the wedge,** never the product or a generic pleasantry.
- **Reply-based intent only.** Never add, suggest, or assume open or click tracking.
- **Simple language** for audiences that are not native English speakers or not tech savvy.

See `references/copy-rules.md` for the full rule set and the reasons behind each.

## The sequence structure

- **Email 1, core context.** The strategy and the reason to reach out now. This is the seller. Most positive replies come from here. Open on the prospect's pain or a shift in their world, then the wedge.
- **Email 2, the platform.** What the product does beyond email 1's hook, and how it makes their life easier. This one is the wingman. It rarely carries the reply on its own, so keep it tight and additive.
- **Email 3, the breakup.** "This is the last time I am reaching out. If now is not the time, tell me and I will circle back. If you are not the right person, tell me who is." This pulls real weight. Replies here are people who were procrastinating and now know it is their last chance.

See `references/sequence-structures.md` for the two-step variant and worked skeletons.

## Subject lines

Name the pain in three to five words. Including the word "your" has lifted response by roughly 15 percent when the pain framing is strong and specific. Treat both as things to A/B test, not laws. See `references/subject-lines.md`.

## After you write

Review the draft in three passes before it ships. First read it as the prospect: would you reply, and what would make you delete it? Second, check it against `company/context.md`: is every claim, number and name one you can actually back? Third, check it against the rules above and the research for the play. Iterate on the feedback. Do not chase a perfect score from every pass at once.

## Deliverable format

The final copy ships as a `.docx` built with python-docx, saved in the play's folder (`plays/<play-slug>/`). Markdown is fine for working drafts, but the version handed off for launch is the docx. Structure it: title and context line up top, list/segmentation rules, then each sequence with subject spintax and body per email, then open items to confirm, then a verified-fact-notes section citing where every number came from (call timestamp, document, or research source). Spintax stays as literal `{{RANDOM|...}}` text.

## The corpus

`references/campaign-patterns.md` and `references/exemplars.md` are distilled from a store of 3,183 campaigns with live copy, 13,337 email steps, and 42,802 categorized replies, with 809 campaigns that earned at least one positive reply. The patterns file carries the measured numbers (body length, sequence length, spintax rates, social-proof placement, reply benchmarks). The exemplars file carries anonymized winning structures rewritten onto fictional companies. Lean on both for angles and structure. Never copy another company's real details into your copy.

One data-backed nuance to hold alongside the hard rules: the 75 to 90 word limit is the discipline for pure cold prospecting. The corpus shows the best campaigns run 110 to 150 words when they carry real social proof (a named customer, a real number). Flex on purpose, with proof, not by accident. See `references/campaign-patterns.md`.
