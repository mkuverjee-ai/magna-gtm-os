---
name: railway-deploy
description: Put a service on Railway in your own Railway workspace - a daily job, a webhook receiver, an internal dashboard, a small API. Use when someone wants to host something, schedule something to run every day, give a script a public URL, or check/redeploy an existing service.
---

# Deploy to Railway (your own workspace)

`reference.md` next to this file is the full skill: Nixpacks layout, Procfile, cron, volumes,
troubleshooting table. This is the short version plus what changes inside the GTM OS.

The workspace token is read with `gtm.cred("RAILWAY_WORKSPACE_TOKEN")` (environment, then
`~/.magna-gtm-config`, then the `api_keys` table). Store it once:

```bash
python3 gtm.py set-key RAILWAY_WORKSPACE_TOKEN     # paste the token on stdin
python3 gtm.py set-key RAILWAY_WORKSPACE_ID        # optional: the workspace new projects go into
```

Create the token at https://railway.com/account/tokens **with the workspace field set** to the
workspace you deploy into. Everything this skill creates lands there.

## The auth model is the whole trick

The Railway **CLI rejects workspace tokens** ([cli#845](https://github.com/railwayapp/cli/issues/845))
but the GraphQL API accepts them. So:

```
workspace token  ->  railway_helper.py (GraphQL): create project, mint a project token
project token    ->  railway CLI: up, variables, domain, logs
```

Never set `RAILWAY_API_TOKEN` to the workspace token. It cannot work.

```bash
R=skills/railway-deploy/railway_helper.py
python3 $R whoami                      # confirms the token and workspace
python3 $R projects                    # every project in the workspace + its services
python3 $R services <project>
python3 $R new <project-name>          # create a project
python3 $R token <project-name>        # mint a project token -> export RAILWAY_TOKEN=...
```

Then the CLI does the deploy:

```bash
export RAILWAY_TOKEN=$(python3 $R token my-service | grep -o 'RAILWAY_TOKEN=[^ ]*' | cut -d= -f2)
cd <isolated copy of the service>
railway up --detach --service my-service
railway variables --service my-service --set KEY=value
railway domain                          # public URL
railway logs --service my-service
```

## Rules that save a wasted hour

- **Copy the service into an isolated folder before `railway up`.** It tars the whole parent tree;
  run it inside a big repo and you get a 413. A `.venv` in the folder will upload too.
- **Bind to `0.0.0.0:$PORT`**, never localhost or a fixed port.
- **`.python-version` must be `3.11`**, not `python-3.11` (the build fails with
  "no precompiled python found").
- **A green `/health` does NOT mean your build shipped.** Poll for a string only the new code
  contains, or put the git commit in `/health`.
- **State needs a volume.** Anything on the normal filesystem dies on the next deploy: SQLite,
  seen-stores, queues, uploaded files. Mount `/data` and point the app at it.
- **A daily job is a cron service** (`railway.json` / the Cron field), not a `while True: sleep`.
  Scheduled runs need `RUNS_DIR` (or equivalent) on the volume, or the dedupe store resets nightly.
- **Secrets go in Railway variables**, never in the repo. If the rest of the team needs the key
  too, store it with `gtm.py set-key` and read it at runtime with `gtm.cred(...)`.

## Before you build anything new

Check `plays/` and the repo for a script or service that already does the job. Reusing one is
hours; rebuilding one is days, and the traps are already paid for.

## Ask before you deploy

Deploying is cheap but not free, and a service that writes to Instantly, Lemlist or a CRM is an
outward-facing system. Tell the user what you are about to create, in which project, and what it
will touch. Live sending or CRM writes need the explicit go-ahead of whoever owns that system.
