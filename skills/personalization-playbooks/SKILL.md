---
name: personalization-playbooks
description: Camp Personalization vs No Personalization playbooks by outreach category - Inbound, Postbound, Bridgebound, and Outbound. Use when deciding personalization level, building automated sequences, or creating messaging templates.
---

# Personalization Playbooks

## Camp Personalization Playbook (Manual/High-Touch)

### INBOUND
```
First Line: Trigger-Based Relevance ONLY
Second Line: CTA to Book Time (Optional: Core-Static Relevance)
```

**Example:**
```
Thanks for downloading [resource name].

Got 15 minutes to discuss how to apply it at {{company}}?
```

### POSTBOUND/BRIDGEBOUND
```
First Line: Trigger-Based Relevance + ("but more importantly") Personalization
Second Line: Personalization "Hook" + Core-Static Relevance
```

**Example:**
```
Saw you attended our webinar on [topic]—but more importantly, your recent post about "[their take]" caught my attention.

You mentioned [specific pain]. We've been helping [ICP] [specific outcome] with [approach].

Worth a quick chat?
```

### OUTBOUND
```
First Line: Personalization Title or Summary + Personalization Excerpt
Second Line: Personalization "Hook" + Core-Static Relevance
```

**Example:**
```
Your post on [topic]—specifically the line "[direct quote]"—resonated.

We work with [ICP] who've hit that wall. Most are shifting from [old approach] to [new approach].

Curious if that's on your radar?
```

---

## Camp No Personalization Playbook (Automated/Scale)

### INBOUND
```
First Line: Trigger-Based Relevance ONLY
Second Line: CTA to Book Time (Optional: Core-Static Relevance)
```

**Example:**
```
Thanks for requesting a demo.

Let's find 15 minutes to walk through how {{product}} works for {{industry}} companies.

[Calendar link]
```

### POSTBOUND/BRIDGEBOUND
```
First Line: Trigger-Based Relevance
Second Line: Core-Static Relevance
```

**Example:**
```
Noticed you've been checking out our pricing page.

We work with [ICP] on [problem].

Worth a quick call to see if there's a fit?
```

### OUTBOUND
```
First Line: Core-Static Relevance (Lean on Pattern Interruptive Opener)
Second Line: Core-Static Relevance ("We work with...")
```

**Example:**
```
Quick question: How's your team handling [problem] right now?

We work with [ICP] who struggle with [specific symptom].

Worth exploring?
```

---

## Decision Matrix

| Factor | Use Personalization | Skip Personalization |
|--------|---------------------|---------------------|
| Deal size | >$25K ACV | <$25K ACV |
| Volume | <50/day | >100/day |
| ICP fit | Tier 1 accounts | Tier 2-3 accounts |
| Signal strength | Weak signals | Strong signals |
| Competitive | High competition | Low competition |

---

## Combines with

| Skill | Why |
|-------|-----|
| `outreach-4-categories` | Match playbook to lead category |
| `personalization-6-buckets` | Find data for personalization |
| `personalization-hooks` | Create hooks for Camp Personalization |
| `cold-email-4-sequence` | Apply playbook to sequence |

## Example prompts

```
Which playbook should I use for a $15K ACV deal with strong intent signal?
```

```
Write a Camp Personalization Bridgebound email for this prospect: [details]
```

```
Create a No Personalization Outbound template for targeting DevOps managers.
```
