# What Can Freckle Do

Use this template to describe Freckle and its current CLI capabilities.

```text
- Build Workbooks: load your rows into a dataset (CSV, pasted records, a webhook feed, or a manual HubSpot contacts/companies/deals import including list selection), wire a workflow to them, and collect the newest result per row in an output dataset.
- Run data through workflows: trigger a workbook connection on demand or automatically as rows arrive, sample-run before full volume, and re-run failures.
- Author lead-enrichment workflows: inspect provider nodes, write typed workflow_draft YAML, validate it through the compiler, and save or publish it.
- Find people with Freckle-provided Apollo access and hand complete person records into a dedicated Dataset by default, or an existing Dataset the user selects.
- Push object collections into same-Workbook Datasets during a workflow run, then chain other workflows from those entries.
- Reuse what exists: list Workbooks with their wiring, list saved workflows with their input/output shapes, export editable drafts, publish new revisions, and update workflow metadata.
- Run workflows on sample inputs: invoke a saved workflow with JSON object inputs and inspect asynchronous run results.
- Manage Workbook datasets: list and create datasets, import CSV or selected HubSpot records, inspect and rerun manual HubSpot imports, manage entries and webhooks, and connect datasets to saved workflows.
- Monitor Dataset Entries for company new hires or contact job changes, route findings into an output Dataset, inspect asynchronous lifecycle progress, and request safe remote cleanup.
- Connect integrations: open Freckle's web app to connect HeyReach, HubSpot, Instantly, or Supabase credentials, list connection status, and inspect public credential IDs.
- Manage CLI setup: authenticate, list available organizations, switch to the org the user chooses, and inspect active API/app endpoints.
```

End by asking whether the user wants to build a workbook for their data, author a workflow, inspect existing workflows or workbooks, connect an integration, or run a saved workflow with sample inputs.
