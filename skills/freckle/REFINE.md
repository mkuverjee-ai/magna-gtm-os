# Work on an Existing Workflow or Workbook

The target already exists and its design is the brief. This route covers operational work such as adding a Dataset or rows and running them, as well as scoped setup changes. There is no plan cycle: locate, inspect, pin, act, verify.

**Fit test:** stay here when the target exists and the request can be completed from its current design plus sensible, reversible defaults. A new Dataset inside a named Workbook is still existing-target work. Escalate to [BUILD.md](BUILD.md) only when the request changes the artifact's overall purpose or requires unresolved choices that alter Workflow shape, providers, outputs, destination, or run behavior. A missing target is a lookup failure, not permission to invent a new one.

Messages speak to a GTM audience, not developers: plain language, translate programming jargon.

## Path

1. **Locate.** Extract ids from Freckle URLs (`/workbooks/<id>`, Workflow equivalents). Check auth and list orgs, then derive the target's org without asking: use `workflow saved list --all` for a Workflow; for a Workbook, run `workbook list --org-id <org-id>` across accessible orgs. On one match, use that Active Organization and continue silently. Ask about org only after zero or multiple matches, showing the lookup result rather than an unfiltered org-choice ritual. After automatic resolution or user selection, pin the Active Organization in the reused shell with `export FRECKLE_ORG_ID=<org-id>`. Do not use `org switch`; it writes shared global config that another agent can overwrite. An explicit command `--org-id` still overrides the environment value.
2. **Inspect before proposing.** Workflow: `workflow saved inspect <workflowId>`, then `workflow saved get-draft <workflowId> --out workflow.yaml` ([cli-reference.md#saved-workflows](workflow/cli-reference.md#saved-workflows)). Workbook: `workbook inspect <workbook-id>` ([WORKBOOKS.md](WORKBOOKS.md)). Also note every connection reading the target Workflow (`workbook list` rows show `workflowId`) — that is what a revision touches.
3. **Pin the change.** Infer intent from the request and inspected artifact. Choose sensible defaults for low-impact details such as fake values, labels, and small sample size. When the target is ambiguous or unresolved choices change shape, providers, outputs, destination, or run behavior, apply the [shared batch grill](SKILL.md#shared-operating-rules) to every currently unblocked decision. Otherwise proceed in the same turn — no todo ceremony, diagram, plan table, objective interview, or approval pause.
4. **Act, contract-first.** For data-only work, follow [WORKBOOKS.md](WORKBOOKS.md) and preserve the Workbook's existing wiring unless asked to change it. For Workflow edits, inspect the full catalog entry of any node you add or reconfigure (`workflow node inspect <definitionKey>`); read [apollo-find-people.md](workflow/apollo-find-people.md) or [push-to-dataset.md](workflow/push-to-dataset.md) when applicable; preview dynamic nodes after config changes; validate the draft, then publish. Mappings, unfold, and output labels are immutable, so a mapping change means a new connection on the same input Dataset.
5. **Verify the blast radius.** If the Workflow's input shape changed, existing connections re-check their mapping at every trigger and can start rejecting — check each one and tell the user. If the output shape changed, output Dataset catalogs do not update themselves — new fields need `dataset catalog replace` to show as columns.
6. **Run only when asked.** When the user wants rows run, apply the sample gate — [WORKBOOKS.md#pending-and-triggering](WORKBOOKS.md#pending-and-triggering) through a connection, [cli-reference.md#run-saved-workflows](workflow/cli-reference.md#run-saved-workflows) for direct invocation.

**Completion** — every box checked:

- [ ] The change is applied and validated.
- [ ] The user is told what changed and what it touches — connections, output columns.
- [ ] Any requested runs went through the sample gate.
