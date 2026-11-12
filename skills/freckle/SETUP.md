# Freckle CLI Setup

Use this reference for auth, organization selection, and active endpoint inspection.

## Auth

`freckle auth` is a device flow you run on the user's behalf whenever auth is missing or expired. It opens the approval page in the user's browser, prints a short one-time user code, and waits up to 15 minutes for approval. The credential lands directly in the CLI's local config; on this path nothing sensitive crosses the terminal or the conversation, and the user code itself is not a secret — show it to the user so they can match it in the browser.

```bash
freckle auth
freckle auth status
freckle auth status --porcelain
```

While the command waits, tell the user to approve the request in the opened browser tab — signing in or creating an account there first is part of the same flow, and if no browser opened, the printed URL gets them there. The command exits 0 once approved; confirm with `freckle auth status`. When device authorization is unavailable, the command reports why; in a shell without an interactive terminal it then exits with token instructions instead of prompting.

Use a token directly when device authorization is unavailable or no browser is available (headless or remote shells); the user creates one at `https://next.freckle.io/cli-auth`:

```bash
freckle auth --token <frk_token>
```

Auth also resolves from `FRECKLE_CLI_TOKEN`.

## Organizations

List organizations:

```bash
freckle org list
freckle org list --token <frk_token>
```

If exactly one organization is available, use it without asking. Otherwise, ask the user to choose from the full list. After automatic resolution or user selection, pin the Active Organization in the reused shell:

```bash
export FRECKLE_ORG_ID=<org-id>
```

Do not use `freckle org switch`; it writes shared global config that another agent can overwrite. An explicit command `--org-id` still overrides this environment value.

## Config

Inspect CLI config and active endpoints:

```bash
freckle config path
freckle config api-base-url
freckle config app-host-url
```
