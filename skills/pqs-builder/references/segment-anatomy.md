# Segment anatomy: the parts of a pain-qualified segment, in our words

Jordan Crawford's framework, distilled in our own words. For his own words, `/edge pqs` (licensed per
person). Never copy Edge text into this repo.

---

## Three kinds of list

| | Firmographic | Pain-qualified segment (PQS) | PVP-ready segment |
|---|---|---|---|
| Defined by | what the company **is** | a situation it is **in** | a situation plus data you can **hand over** |
| Example | US fintech, 100-500 staff | hired a second SDR in 60 days, nobody runs the team | same, plus the first 8 accounts for that rep, already built |
| Changes over time? | rarely | yes, it has a half-life | yes |
| Competes on | copy (everyone has the list) | data | the gift |
| Message | a pitch | "here's what I see, am I reading it right?" | the value itself |

This skill produces the middle column. `/pvp-builder` takes the best of them to the right-hand column.
A PQS is not a lesser PVP. It is the right answer when the evidence proves the pain is likely but does
not, on its own, give the buyer something to act on.

## The five parts

### 1. Situation
One sentence a ten-year-old understands, describing something that **happened to** the company.

- Good: "They posted a second SDR role in the last 60 days, and nobody on LinkedIn manages the SDRs."
- Bad: "Scaling B2B SaaS companies investing in outbound." (A trait and a vibe.)

### 2. Tension (H1 against H2)
Two facts pulling against each other. One signal is noise; the pull is the pain.

| H1 (what they are doing) | H2 (what makes it hurt) | The pain |
|---|---|---|
| Hiring reps | No one to run them, no ranked accounts | New rep starts with nothing to work |
| Paying for a data tool | Renewal date approaching, no measured value | Has to defend a line item without evidence |
| Upgrading SQL Server | MDS is not in SQL Server 2025 | Master data has to move first |
| Launching to a new buyer | Ads still target the old buyer | Spend going to the wrong people |

If you cannot write H2, you have a signal, not a segment. Keep looking, or drop it.

### 3. Amplifier
What makes it hurt **now**: a deadline, a quarter target, a start date, a regulation date, a season.
Use the true date, not the scariest one (MDS on SQL Server 2022: mainstream support to 2028, extended
to 2033; leading with 2028 alone read as manufactured urgency).

### 4. Existential data point (EDP)
The number that, past a threshold, costs someone their job, the company a contract, or the quarter.

- **Existential**: "is this real?" from a CFO. Revenue, compliance, the reader's job.
- **Incremental**: "so what?" from a CFO. Efficiency, nice-to-have.

Incremental segments can still run, but they compete with every other efficiency pitch. Label them.
A good EDP usually has a sweet spot: too low means they already solved it, too high means it is past
saving. Mapping the EDP against a second axis often splits one segment into two or three.

### 5. Membership test
Every condition as `source.field operator value`, tagged **public / proxy / not public**. The test is
what makes the segment rebuildable by someone who was not in the room. See SKILL.md phase 3.

## Half-life

Every segment decays. Write down how long a row stays true and re-pull on that cadence.

| Fingerprint | Typical half-life |
|---|---|
| Job post | 30-60 days (closed or filled) |
| New leader in seat | ~90 days of "new" |
| Funding round | 6-12 months of spend pressure (never an opener) |
| Filing / regulation deadline | until the date |
| Tech adoption (first-seen) | months; useful as a proxy, not a fact |
| Review / complaint spike | weeks |

## Where segments come from (in order of trust)

1. **The moment a real customer bought.** What was true about them in the 90 days before? Provable
   from public data?
2. **Your sales calls with prospects, and replies to your campaigns.** What made them take the call
   or answer, in their words.
3. **Closed-lost and churn.** The situation where you cannot win is as useful as where you can.
4. **The team's beliefs** (the ICP in `company/context.md`, positioning docs, strategy calls).
   Starting hypotheses, labelled `[team belief]` until the data agrees.
5. **Your own ideas.** Last, and only if the backtest supports them.

## Who feels it, who signs

Name the title that owns the pain and say whether that person can sign. When the champion cannot sign,
the segment's message has to survive being forwarded: in one measured set of B2B sales calls, about 8
of 19 ended with "send me something I can show my CEO or board".

## Questions for the call

Anything **not public** that matters (contract dates, budget, internal tooling, headcount plans)
becomes a qualifying question for the first call, written down per segment. A segment is allowed to
have them; it is not allowed to rest on them.
