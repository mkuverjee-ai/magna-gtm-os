# Waterfalls

An enrichment waterfall runs structured providers in order of precision, falls back on insufficiency, and ends in a Research Agent backstop. When reading an existing Workflow, recognize this shape before editing it: provider branch cases, per-fallback branches, a convergence collector, and a final all-fallbacks-failed output are the waterfall — they survive an edit intact unless the request explicitly changes the fallback design.

## Construction

- Primary: the most precise structured provider for the pinned objective.
- Branch on insufficiency: each fallback provider runs only on its fallback branch, strictly after the rung above it misses.
- Final fallback: Research Agent, per [research-agent.md](research-agent.md). Every waterfall gets its own backstop — including a mid-Workflow waterfall that recovers an identifier (a LinkedIn URL, a domain). A Research Agent elsewhere doing a different job (scoring, summarizing, verifying at the end) is not the backstop: a missed identifier starves every structured provider downstream of it, and a tail agent cannot resurrect that chain — only a backstop inside the waterfall keeps it alive.
- Converge fallback outputs through one collector at the earliest shared value, then continue with a single downstream chain — duplicating a downstream provider per branch is node bloat. See [collector.md](collector.md), including its re-gating pattern.
- Plan the all-fallbacks-failed path: what the Workflow emits when every provider comes up empty.
- Skip a fallback only when its contract does not fit the pinned objective, the node is unavailable in the destination org, or the user explicitly chose a different fallback policy.
