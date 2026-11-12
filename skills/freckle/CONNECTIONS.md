# Freckle Integration Connections

Use this reference when the user wants to connect provider credentials.

List connectable integrations and inspect public credential summaries:

```bash
freckle connections list
freckle connections list --json
freckle connections show hubspot
freckle connections show heyreach
freckle connections show hubspot --json
freckle connections show contactout --json
```

When a Workflow node config accepts a `credentialId`, inspect its node contract to identify the integration
and whether the node supports managed access. Select an authorized credential from
`freckle connections show <integration> --json` and set that exact ID while preserving the node's
other config fields. If the selected credential is unavailable, ask the user to reconnect or select another;
use managed access only when the node contract supports it and the user chooses it. Use the Workflow cost
estimate for Freckle credit cost; charges from a customer-owned provider account are separate.

Open the Freckle web app to connect one supported integration:

```bash
freckle connections connect heyreach
freckle connections connect hubspot
freckle connections connect instantly
freckle connections connect supabase
freckle connections connect contactout
```

The command prints the URL and tries to open a browser.

Apollo Find People currently uses Freckle-provided access and does not require a customer Apollo connection or `credentialId`; see [workflow/apollo-find-people.md](workflow/apollo-find-people.md).
