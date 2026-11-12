---
name: campaign-delivery
description: A 9-phase campaign build checklist, kick-off through deploy and learn. Use when planning or shipping an outbound campaign (a play).
---

# Campaign Delivery

Build outbound campaigns from scratch with a 9-phase system. Based on Jordan Crawford's methodology (Blueprint GTM).

Each campaign is a **play**: one segment or campaign, living in `plays/<play-slug>/` with `research/`,
`leads/companies/`, `leads/contacts/`, `campaigns/` and `reports/`. Company-wide context (ICP, positioning,
proof, personas, offers) is in `company/context.md`.

---

## Golden Rule

> Write the perfect email FIRST, then build the list that makes it true.

Copy (Phases 2-3) comes BEFORE list building (Phase 5). The list should be defined by who the email literally describes.

---

## The 9-Phase Checklist

### Phase 0: Kick-Off (FREE)

- [ ] Name the campaign (descriptive, not clever)
- [ ] Define who we are targeting and why NOW
- [ ] Identify the "tension" -- two data points pulling in opposite directions
- [ ] Create `plays/<play-slug>/` and document in `plays/<play-slug>/campaigns/campaign-brief.md`

**Tension Triangle:**
```
        [Growth Amplifier]
             /\
            /  \
           /    \
[Heuristic 1] --- [Heuristic 2]
```

Example: No SDR headcount (H1) + Revenue growth slowing (H2) + Recent funding (Amplifier)

---

### Phase 1: Context (FREE)

- [ ] Read `company/context.md` (`python3 gtm.py company` prints it plus which keys are set)
- [ ] Read the ICP matrix / scoring model and any `/pqs-builder` or `/pvp-builder` output in `plays/*/research/`
- [ ] Read what already worked or failed: `python3 gtm.py intel`
- [ ] Read past campaign performance data and real reply bodies (Instantly / Lemlist, read-only)
- [ ] If you record calls: `python3 gtm.py meetings` / `gtm.py transcript --date YYYY-MM-DD` for buyer language, objections, triggers
- [ ] Summarize all context into `plays/<play-slug>/campaigns/campaign-context.md`

**Context compounds.** Every campaign you build makes the next one smarter.

---

### Phase 2: Angles (FREE)

- [ ] Map the core tension (why does this prospect need us NOW?)
- [ ] Brainstorm 5-10 different email angles
- [ ] Classify each angle as PVP or PQS (see below)
- [ ] Rank angles by strength of tension + data availability
- [ ] Document in `email-variants.md`

**PVP (Permissionless Value Prop):** Deliver an insight that is independently valuable. The prospect would pay to receive your email even if they never buy.

Example: "Found 7 people featured in your case studies who started new roles in the last 6 months. That's approximately $400K in warm pipeline. Want the complete list?"

**PQS (Pain-Qualified Segment):** Identify prospects in the exact same painful situation as existing customers and tell them how those customers navigated it.

Example: "Most founders I talk to at the {{companyName}} stage built their business on referrals. It works -- until it doesn't scale."

**PVP > PQS always.** Only fall back to PQS if you cannot build a true PVP.

---

### Phase 3: Copy (FREE)

- [ ] Write 5-10 Email 1 variants (one per angle)
- [ ] Write full follow-up sequence (3-4 steps) for top 2-3 variants
- [ ] QA every email against the 21-check quality system (10 house + 11 Crawford)
- [ ] Run "Would I Reply?" test on each email
- [ ] Document all variants in `email-variants.md`

**Crawford Quality Checks (11):**
1. Does it pass the "so what?" test?
2. Is the tension real and observable?
3. Is the PVP independently valuable?
4. Is the data verifiable (not made up)?
5. Is the CTA a genuine question (not a disguised pitch)?
6. Does it sound like a human wrote it?
7. Is it under 100 words?
8. No "I noticed" or "I saw" openers?
9. Does every sentence earn the next?
10. Would you forward this to your boss?
11. Does the subject line earn the open without clickbait?

**House Quality Checks (10):**
1. No generic intros ("Hope this finds you well")
2. No feature dumping
3. Personalization feels natural, not forced
4. CTA is low-friction (question, not meeting request)
5. Multi-variant testing built in (5-10 Email 1s)
6. Follow-ups add new value (not "just following up")
7. Sequence has logical escalation
8. Unsubscribe language included
9. No more than 1 link per email
10. Mobile-readable (short paragraphs, no walls of text)

---

### Phase 4: Targeting (FREE)

- [ ] Define exact list criteria that make every email TRUE
- [ ] Specify company filters (size, industry, location, funding, tech stack)
- [ ] Specify contact filters (title, seniority, department)
- [ ] Specify signal filters (hiring, news, job changes)
- [ ] Specify exclusions (wrong industry, too big/small, existing customers)
- [ ] Document in `plays/<play-slug>/campaigns/list-criteria.md`

"The list IS the message." Every filter should exist because the email references or implies that criteria.

---

### Phase 5: List Building (COSTS MONEY -- ask first)

- [ ] Size first with a free/cheap count (AI Ark preview, see `ai-ark` / `icp-tam-mapper` skills)
- [ ] Pull accounts from AI Ark matching Phase 4 criteria -> `plays/<play-slug>/leads/companies/`
- [ ] Enrich with company data (industry, size, revenue, funding)
- [ ] Score and tier companies (see `tam-scoring` skill)
- [ ] Pull contacts at qualified companies -> `plays/<play-slug>/leads/contacts/`
- [ ] Find and verify emails (AI Ark, see the `ai-ark` skill)
- [ ] Deduplicate, including against existing customers and open deals (see `list-dedup` skill)
- [ ] Export to campaign-ready CSV

**Always confirm budget before running enrichments.** Tell the user exactly what API calls you are about to make and the estimated cost.

**Start small:** Test on 25-50 accounts before running on 1,000+.

---

### Phase 6: Personalization (MAYBE COSTS MONEY)

- [ ] Generate personalized opening lines or custom signals per prospect
- [ ] Use Clay/Claygent or script-based approach
- [ ] Fill in template variables ({{location_count}}, {{pe_firm}}, etc.)
- [ ] Verify personalization is accurate (spot-check 20 rows)

**Cost depends on approach:**
- Claygent with your own OpenAI API key = near-free
- Clay enrichment columns = Clay credits
- Manual/script-based = free

---

### Phase 7: QA (FREE)

- [ ] Spot-check 20 random rows from the final spreadsheet
- [ ] Verify: Is the data accurate? Is the personalization correct?
- [ ] Run deliverability check (email verification status)
- [ ] Run "Would I Reply?" test on 5 fully-personalized emails
- [ ] Flag and fix any bad rows

---

### Phase 8: Deploy (FREE)

- [ ] Load CSV into Instantly or Lemlist
- [ ] Configure sequence (steps, delays, sending schedule)
- [ ] Assign inboxes to campaign
- [ ] Send test emails to yourself / team
- [ ] Review test emails on mobile and desktop
- [ ] Launch (start with small daily volume, ramp up)

---

### Phase 9: Learn (FREE)

- [ ] Pull performance data after 7 days, 14 days, 30 days
- [ ] Document: open rate, reply rate, positive reply rate, meeting rate
- [ ] Identify winning variants vs underperformers
- [ ] Write learnings into `plays/<play-slug>/reports/campaign-learnings.md`
- [ ] Log each learning so the next play starts from it: `python3 gtm.py log-intel --play <play-slug> --category ... --label ... --insight ...`
- [ ] Feed durable learnings (proof, objections, personas) back into `company/context.md`

---

## Timeline

| Phases | Time | What |
|--------|------|------|
| 0-4 | 2-3 hours | Context through copy (all free) |
| 5 | 1-3 hours | List building (costs money) |
| 6-7 | 1-2 hours | Personalization + QA |
| 8 | 30 min | Deploy |
| 9 | Ongoing | Learn and iterate |

**Total: ~half a day for a campaign that used to take a week+.**

---

## Key Principles

1. **Every step produces a file.** Nothing stays in your head.
2. **Context compounds.** Every campaign makes the next one better.
3. **Copy before list.** Write the perfect email, then build the list.
4. **Files first.** Every list and every email exists as a reviewed file before anything is loaded into a sender or written to the CRM.
5. **The system asks before spending.** Any step that costs money requires explicit approval.
6. **Start small, test, then scale.** 25 accounts before 1,000. 5-10 variants before picking a winner.

---

## File Structure Per Campaign

```
plays/{play-slug}/
  research/                  -- PQS / PVP output, segment research
  leads/companies/           -- Phase 5: account lists
  leads/contacts/            -- Phase 5: contact lists
  campaigns/
    campaign-brief.md        -- Phase 0: what and why
    campaign-context.md      -- Phase 1: all context summarized
    email-variants.md        -- Phases 2-3: angles + copy
    list-criteria.md         -- Phase 4: targeting spec
  reports/
    campaign-learnings.md    -- Phase 9: performance + insights
```

---

## References

- Crawford Method: `skills/crawford-method/SKILL.md`
- Copy: `skills/copywriter/`, `skills/cold-email-copy/`, `skills/josh-braun-copywriting/`
- Segments and offers: `skills/pqs-builder/`, `skills/pvp-builder/`
- Lists: `skills/ai-ark/`, `skills/icp-tam-mapper/`, `skills/tam-scoring/`, `skills/list-dedup/`
- Sending: `skills/instantly/`, `skills/lemlist/`
- Company context: `company/context.md` (`python3 gtm.py company`)
- What worked before: `python3 gtm.py intel`
