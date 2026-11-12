# Gift archetypes

A menu, not a checklist. Each archetype says **what the buyer gets**, **what it needs from you**,
and **an example of the shape** (drawn from real campaigns, names removed). Adapt it to your buyer's
EDP. Don't paste an archetype in unchanged.

---

## Bucket 1: Proprietary data exhaust (strongest moat)

### 1a. The benchmark only they can compute
The prospect's number next to the distribution across your customer base. "Your listing
conversion is in the bottom quartile of the 380 hotel sites we track."
- Needs: aggregate data across ≥10 customers, a public or inferable number for the prospect.
- Legitimacy: aggregated and anonymised, cohort n≥10, and internal (often legal) sign-off on using it.
- Example: reply-rate benchmarks across ~550 B2B campaigns (median 0.64%, p90 2.75%) sent by an
  outbound vendor; a paid-ads agency's anonymised top ads by industry (past/inactive customers first).

### 1b. The anonymised winners file
"The 5 ads / subject lines / landing pages that performed best in your category over the last 90
days, with the metric." It comes from your own performance data, with identifiers stripped.
- Example: a paid-ads agency's best-performing ads by category; an outbound vendor's large archive of
  campaign snapshots ("what messaging gets replies in your space").

### 1c. The rate or price table
What the market actually pays or charges, drawn from your transaction flow. Existential when
the prospect is visibly off-market.

---

## Bucket 2: Expert capability (the done-for-you slice)

### 2a. Remake / redo
Take the prospect's asset (or their competitor's proven one) and remake it. The finished thing is the gift.
- Example: a paid-ads agency remakes a competitor's top 5 Meta ads with the prospect's logo. "You keep
  them either way." Gated to the top tier (50+ active ads) because design capacity is finite.

### 2b. Teardown with the fix
A specific audit of one live asset (landing page, call funnel, onboarding email, pricing page) with
the three fixes ranked. Useful because the fixes are concrete.
- Example: a call-funnel audit against a proven playbook (step one of the fix only); an Amazon-listing
  audit ("the 5 things you should be doing").

### 2c. The built system, handed over
A working thing configured for them: a scoring model, a dashboard, a sequence, a pilot environment.
- Example: "I built a version of this for your company, want to see it?" It works because the thing exists at send time.

### 2d. Proof on request
When the prospect asks for evidence, you hand over the evidence (the exact prompts, the sources, the
5 fixes) and don't push for a call.
- Example: for one AI-search agency, "send me the proof over email" was the most common positive reply,
  so the reply hands over the evidence.

---

## Bucket 3: Vantage point

### 3a. Voice of *their* customer
Everything the prospect's customers say in public (reviews, Reddit, comments, forums), synthesised
into what they love, what they hate, and the exact phrases. It becomes an ad-hook or positioning gift.
- Example: a customer-voice report per DTC brand (reviews, Reddit, social), measured at ~$0.66-1.36
  of data collection per brand plus an LLM synthesis pass.

### 3b. Who's moving in their market
Switchers, churners, new entrants, expansions, as seen from where you sit.
- Example: lookalikes of a won account (`ocean-lookalike`); technology-detection style "every customer
  of vendor X".

### 3c. Proof-by-naming-three
Three of the prospect's own customers, each with a specific observation the prospect didn't know.
This shape survives cold inboxes very well, and it needs a reliable way to find the prospect's customers.

---

## Bucket 4: Public data read with expertise

### 4a. The competitor gap
What their named competitors do that they don't, with evidence: ads (with run length + variant count
as a performance proxy), content, hiring, pricing pages.
- Example: a competitor Meta ads gap report (`meta-ad-counts` for the counts); a LinkedIn ads teardown.

### 4b. Their own footprint, mapped
Something about their own company they've never seen written down: sending-domain estate, DMARC gaps,
tech stack, a role reposted three times since August.
- Example: a map of their cold-sending domain estate (lookalike domains, shared nameservers, DMARC gaps)
  built from public DNS.

### 4c. The list is the gift
A list of accounts or people in *their* market, filtered on one signal they care about. "I pulled the
CFOs who started in the last 30 days at US companies with EU subsidiaries. Want it?"
- Example: a one-signal list built with the Exa Agent. Measured: 50-person list = $3.33 / ~10 min.
  ONE filter, never stacked.

### 4d. The regulatory / record window
A dated public record that creates a deadline: a permit, citation, filing, rate change, contract expiry,
or court docket. It's the most existential archetype when it fits.
- Example: court dockets for a legal-marketing vendor; hotel openings and renovations for a hospitality
  agency.

### 4e. The TAM, counted
A real number for *their* market ("2,400 heads of sales at 51-200 person German SaaS"). It's weak
alone (G3 often fails) but a strong add-on to 4c.

---

## Picking the delivery mode

| Mode | Use when | Watch out for |
|---|---|---|
| Insight in email 1 | Per-row data is available at send time | Needs a Clay/engine column per prospect |
| Named, delivered on yes | The artifact is expensive but already built per prospect | "Could build" is a pitch, so it must exist |
| Self-serve page | The prospect supplies the input (transcripts, CSV) | Bigger companies won't upload first-party data cold |
| Step 2 attachment | Email 1 names it, email 2 delivers it unasked | Deliverability: links/attachments in cold step 1 hurt |
