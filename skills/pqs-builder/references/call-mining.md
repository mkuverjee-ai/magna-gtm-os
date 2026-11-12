# Call mining: from transcripts to buying moments and a language bank

The calls are the cheapest ground truth there is. What we want from them is narrow: **what was true at
the moment this company decided to talk or buy, and how they said it.**

---

## Getting the transcripts

| Where | How | Notes |
|---|---|---|
| GTM OS | `python3 gtm.py meetings [--limit N]` then `gtm.py transcript --date YYYY-MM-DD` | Reads the calls stored in your own database; start here |
| Play folders | `plays/<play-slug>/research/` | Earlier mining notes and saved call summaries. Some are summaries, not transcripts; say which |
| Fireflies MCP | the `mcp__fireflies__*` tools (search, then get transcript / summary) | When connected; see the `fireflies-mcp` skill |
| Other call recorders (Gong, Chorus) | An export or read-only access | Same schema applies |
| Campaign replies | Instantly / Lemlist reply bodies, read-only (keys via `gtm.cred(...)`) | The buyers' own words, unprompted. The main source when few calls are recorded |
| Win-loss notes | CRM closed-won / closed-lost reasons | The moment of purchase, in your reps' words |

**No transcripts, or only a few?** Recordings are often confidential or sparse. Run the same schema
over reply threads and win-loss notes instead, and say so in the doc. The language bank gets thinner,
so lean harder on the customer backtest in phase 5.

Record which calls you used and which you skipped (internal syncs, no-shows, wrong company) with a
count. "100 prospect conversations out of 125 transcripts" is a finding the reader needs.

## Batching

- Under ~15 transcripts: read them yourself.
- More: one general-purpose subagent per batch of ~20, all in parallel, the same prompt and schema.
  Each writes `plays/<play-slug>/research/pqs/mining/batch-N.md` and returns only a short summary.
- Long transcripts: pass the file path, not the text. Let the subagent read it.
- Then one synthesis pass across all batches: cluster the moments, count each cluster.

## The subagent prompt

```
You are mining sales-call transcripts for <COMPANY>, which sells <ONE LINE> to <BUYER>.
Read every transcript in: <PATHS>. Skip internal calls and no-shows; list what you skipped and why.

For each PROSPECT or CUSTOMER call, write:
- Company (domain), date, who spoke (name, title), call type (first call / demo / proposal / renewal)
- Situation: what was true for them at this moment, one sentence
- Why now: what changed recently that made them take the call. Quote it.
- Already tried: tools, agencies, hires, and how it went
- Verbatim pain: 2-4 exact quotes with the speaker. Copy them exactly, do not tidy them.
- Outside-in fingerprint: what a stranger could have seen BEFORE this call that pointed at this
  situation (a job post, a filing, a tool on their site, an ad, a hire, a funding round, a review).
  Say "none visible" if nothing would have been.
- Who can sign: was the person on the call the buyer? If not, who is?
- Outcome if known: bought / lost / stalled, and the reason given

Then, across the batch:
- Group the situations that repeat. For each group: a name, the companies, the count.
- Language bank: the phrases buyers used for the pain, with speaker, company and date.
- Anything that contradicts what <COMPANY> believes about its buyers: <BELIEFS FROM CONTEXT PACK>.

Rules: quote, never paraphrase, in the verbatim fields. No guesses about anything not said; write
"not stated". Do not invent counts. Save to <OUTPUT PATH> and return a 10-line summary.
```

## What to pull out at synthesis

1. **Buying moments table**: moment, count, companies, the strongest quote, the outside-in fingerprint.
2. **Language bank**: phrase, who, company, date, which segment it belongs to. Used in phase 7.
3. **Contradictions**: where the calls disagree with the team's beliefs. These are often the best
   segments, because nobody else is targeting them.
4. **Cross-cutting facts** that shape every segment (who signs, the real competitor, the budget shape).
   Measured example: in one set of ~100 calls, "we'll build it ourselves with an AI assistant" was the
   main competitor in about a third of them.
5. **Lost and stalled reasons**: the situations where you cannot win, to exclude.

## Language bank rules

- Borrow the vocabulary, never the quote. A named prospect's line never appears in another prospect's
  inbox.
- Keep our jargon out ("ICP", "signal", "PQS", "pain segment"). Buyers do not talk like that.
- Keep the speaker's role: a VP's words land with VPs; a founder's with founders.
- A phrase that came up in three or more calls beats a vivid one from a single call.

## Traps

- **Summaries are not transcripts.** An AI meeting summary has already paraphrased; quotes from it are
  not verbatim. Say when you only had summaries.
- **The loudest call is not the pattern.** Count before you rank.
- **Internal strategy calls** tell you what the team believes about buyers, not why buyers buy.
- **Speaker labels drift** in transcripts (ASR swaps names). Check who is speaking from the content
  before attributing a quote.
