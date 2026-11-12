# GTM OS test dashboard

A live page for testing the GTM OS beside the Outbound Machine, without changing the machine.

- **Live page:** a claude.ai Dashboard artifact (link in the team's records).
- **Reads, never writes:** the machine's `campaign_plan`, campaign history (Instantly lifetime totals) and Coach learnings.
- **OS-owned tables (n8n):** `gtm_os_plays` (test plays) and `gtm_os_tests` (the six tests). Nothing in the machine reads them.
- **Skills:** `skills.json`, the 60 skills with stage and your use/adapt/skip call.

## Sections

| Section | Shows |
|---|---|
| Plays | OS test plays as cards (segment, offer, success bar, results) and the machine's campaign plan as plays |
| Results vs benchmarks | Every campaign's reply rate against the median 0.64% and top decile 2.75% |
| Tests | The six tests: arms, size, win rule, what each needs, status, result |
| Playbook | The 60 skills, filterable by call |
| What worked | The Coach's current learnings |

## Files

- `index.html`: the page (Dashboard type, one-writer rule).
- `datasets/*.json`: where each number comes from.
- `skills.json`: the Playbook data.

To change the page, edit `index.html` and write it to the artifact's `files/index.html`.
