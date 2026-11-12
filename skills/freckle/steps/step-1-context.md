# Step 1: Context Selected

Select the destination Active Organization for this work explicitly, even when shared global config already names one.

- Check auth: `freckle auth status`. Not authenticated → run the device flow in [../SETUP.md](../SETUP.md#auth), then re-check.
- List every org the user can access: `freckle org list`.
- Exactly one org: select it without asking, tell the user which org you're working in, pin it as described below, then move on.
- Request names an existing Workflow or Workbook (by URL, id, or name): extract any id from the URL and derive the org from where that resource lives instead of asking.
  - Workflow: `freckle workflow saved list --all` — results are grouped by org; find the Workflow whose id or label matches.
  - Workbook: run `freckle workbook list --org-id <org-id>` for each org from `org list`; find the Workbook whose id or label matches.
  - Exactly one match: select its org, tell the user which org you're working in and which Workflow or Workbook you found, pin it as described below, then move on.
  - Zero or multiple matches: say what you searched for and what you found, then fall back to asking below.
- More than one org and no derived match: present the full org list to the user as a Markdown table and ask which org they want to work within. The user may answer with the org name; map it back to the listed `orgId`. If multiple orgs match, ask before selecting.
- After automatic resolution or user selection, pin the Active Organization in the reused shell: `export FRECKLE_ORG_ID=<org-id>`. Do not use `freckle org switch`; it writes shared global config that another agent can overwrite. An explicit command `--org-id` still overrides this environment value.

**Completion** — every box checked:

- [ ] The destination Active Organization is selected — auto-selected as the only org, derived from the Workflow or Workbook the request names, or chosen by the user from the full org table.
- [ ] The user has been told which org you're working in.
- [ ] `FRECKLE_ORG_ID` is exported in the reused shell.

Completion met → read [step-2-objective.md](step-2-objective.md).
