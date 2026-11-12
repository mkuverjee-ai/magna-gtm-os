---
name: freckle
description: "Use when the user asks to use the Freckle CLI or get Freckle to do something: enrich/score/process a lead list, build or change Workbooks, datasets, or Workflows, publish or run saved workflows, inspect node capabilities, auth/org/config setup, or integration connections."
---

# Freckle

Freckle is optional in this OS. Use it only if you have a Freckle account and the `freckle` CLI is
authenticated (`freckle auth status`, see [SETUP.md](SETUP.md)); otherwise source with `skills/ai-ark`.

This is a router skill: pick exactly one route below and load only that reference. Load the route's file before running any `freckle` command — even `--help`; the route files tell you which commands to run and when.

**New builds are gated.** Route work with no existing target to [BUILD.md](BUILD.md). When the request identifies an existing Workbook or Workflow by URL, id, or name, route to [REFINE.md](REFINE.md) instead: locate the target, derive its org, and work from the design already embodied there. REFINE owns the fit test and escalates only a genuine redesign or a shape-changing ambiguity.

## Route

| User wants | Load |
| --- | --- |
| Get Freckle to do something with no existing target — enrich, score, look up, run data, or build a Workbook or Workflow | [BUILD.md](BUILD.md) |
| Do anything to an existing Workbook or Workflow identified by URL, id, or name — add data, run rows, or change its setup | [REFINE.md](REFINE.md) |
| Run an existing saved Workflow directly with JSON inputs, inspect runs, list saved Workflows | [workflow/cli-reference.md](workflow/cli-reference.md) |
| Inspect node capabilities | [workflow/cli-reference.md#node-catalog](workflow/cli-reference.md#node-catalog) |
| Workbook housekeeping that changes nothing about what runs — inspect, archive, delete entries, rotate webhook secrets | [WORKBOOKS.md](WORKBOOKS.md) |
| Create, inspect, list, or delete Dataset Signals | [SIGNALS.md](SIGNALS.md) |
| Log in, check auth, choose org, inspect endpoints | [SETUP.md](SETUP.md) |
| Connect ContactOut, HeyReach, HubSpot, Instantly, or Supabase, or find credential IDs | [CONNECTIONS.md](CONNECTIONS.md) |
| Understand enrichment waterfalls, collectors, or Research Agent usage | [workflow/waterfall.md](workflow/waterfall.md), [workflow/collector.md](workflow/collector.md), [workflow/research-agent.md](workflow/research-agent.md) |
| Explain what Freckle can currently do — a capability question only, with no task attached | [WHAT-CAN-FRECKLE-DO.md](WHAT-CAN-FRECKLE-DO.md) |

## Shared Operating Rules

- When user decisions are needed, run a **batch grill**. Map the decisions as a design tree and work it in rounds. The frontier is every decision whose prerequisites are settled: ask the whole frontier in one round, number every question, and give your recommended answer for each, then wait for the user's answers. A decision that depends on another unsettled answer waits for a later round. After each reply, recompute the frontier. The grill is complete only when the frontier is empty: every shape-changing branch has been visited and nothing remains silently assumed. Make changes or run data only after the user confirms shared understanding; a route's later approval gate may supply that confirmation.
- Facts are agent work. Resolve anything available from the CLI, filesystem, inspected artifacts, catalogs, or other tools instead of asking the user. If a lookup can run independently, dispatch it and ask the rest of the frontier while it runs; only decisions downstream of that lookup wait.
- Resolve the org from any named resource before asking the user. Confirm the active org only when the request supplies no resource from which to derive it. Auth-only, config-only, and generic product-capability answers need no org setup.
- After automatic resolution, user selection, or an explicitly supplied org, pin `export FRECKLE_ORG_ID=<org-id>` in the reused shell for every routed org-scoped command, and preserve an explicitly supplied org. An explicit command `--org-id` takes precedence over `FRECKLE_ORG_ID`. Do not use `freckle org switch`; it writes shared global config that another agent can overwrite.
- Confirm unfamiliar flags with `freckle <subcommand> --help` before running a command your route file prescribes.
- Use absolute `--file` paths when possible; package scripts can change relative resolution.
