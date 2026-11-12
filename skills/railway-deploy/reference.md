# Deploy to Railway: full reference

Take any local folder and get it running on the internet in your own Railway workspace, with a
public HTTPS URL. The only credential is a workspace token you create once (see Credentials below).

**Workspace:** whichever workspace your `RAILWAY_WORKSPACE_TOKEN` was created for (optionally
pinned with `RAILWAY_WORKSPACE_ID`). Everything this skill creates lands there.

---

## The auth model - read this once, it explains everything

Railway has three token types. Two matter here, and they are **not interchangeable**:

| Token | Scope | Works with | Used for |
|---|---|---|---|
| **Workspace token** | one whole workspace | GraphQL API only | creating projects, minting deploy tokens, listing |
| **Project token** | one project + one environment | the `railway` CLI | `up`, `variables`, `domain`, `logs`, `status` |

The catch: **the Railway CLI rejects workspace tokens** ([railwayapp/cli#845](https://github.com/railwayapp/cli/issues/845)) -
they authenticate fine against GraphQL but the CLI returns `Unauthorized`. This is a Railway
bug, not a bad credential. So the flow is always:

```
workspace token ──(railway_helper.py)──> project token ──(railway CLI)──> deployed
```

`railway_helper.py` in this folder wraps the GraphQL half. You never need to touch GraphQL by hand.

> Do **not** try to fix an `Unauthorized` from the CLI by re-minting the workspace token or by
> setting `RAILWAY_API_TOKEN`. That path cannot work. Get a project token instead (below).

---

## Setup (once per machine, ~20 seconds)

```bash
railway --version || npm i -g @railway/cli
```

Store the workspace token (once), then verify it from the skill folder:

```bash
python3 gtm.py set-key RAILWAY_WORKSPACE_TOKEN    # value on stdin
python3 gtm.py set-key RAILWAY_WORKSPACE_ID       # optional
```


```bash
python3 railway_helper.py whoami
```

Expected:

```
Workspace: <your workspace id, or "inferred from the token">
Token is valid. N project(s) visible.
```

If that prints, you are done - there is no `railway login`, no browser step, no device code.

---

## Deploy something new (the main path)

Four commands. Say the project is a Python API in `~/work/my-api`.

**1. Create the project and get a deploy token**

```bash
python3 skills/railway-deploy/railway_helper.py new my-api
```

Prints the project id and an `export RAILWAY_TOKEN=...` line. Copy it.

**2. Make sure the folder is deployable** - see [What a deployable folder looks like](#what-a-deployable-folder-looks-like) below.

**3. Deploy**

```bash
cd ~/work/my-api
export RAILWAY_TOKEN=<token from step 1>
railway up --detach
```

`--detach` returns immediately instead of streaming build logs. `railway up` auto-creates the
service on first deploy - you do not create one separately.

**4. Give it a public URL**

```bash
railway domain
```

Returns `https://my-api-production.up.railway.app`. Only do this for something that serves
HTTP. A background worker or cron job should not get a domain.

Then confirm the build actually succeeded before reporting success:

```bash
railway deployment list        # want SUCCESS, not BUILDING or FAILED
curl -s https://my-api-production.up.railway.app | head
```

---

## Deploy to a project that already exists

```bash
python3 railway_helper.py projects              # find the name
python3 railway_helper.py token my-api          # mint a deploy token for it
cd ~/work/my-api
export RAILWAY_TOKEN=<token>
railway up --detach --service my-api             # --service matters if there are several
```

`python3 railway_helper.py services my-api` lists the services and environment ids in a project.

---

## Environment variables

```bash
railway variables                                          # read all
railway variables --set "ANTHROPIC_API_KEY=sk-ant-..."     # set one, triggers a redeploy
railway variables --set "FOO=1" --set "BAR=2" --skip-deploys   # set several, no redeploy
```

`--skip-deploys` is the right default when setting a batch - set them all, then deploy once.

Variables live on the **service**, per environment. They are not in the repo, so a fresh deploy
of the same code into a new project starts with none of them. When moving a service, read the
old one's variables first and carry them over.

Reference another service's variable with `${{other-service.VAR}}`; reference Railway's own with
`${{RAILWAY_PUBLIC_DOMAIN}}`.

---

## Logs, status, redeploy

```bash
railway status                    # which project/env/service am I pointed at
railway logs --build              # build output - start here when a deploy fails
railway logs --deployment         # runtime output - start here when it built but 502s
railway deployment list           # deploy history + status
railway up --detach               # redeploy: just push again
railway down                      # remove the most recent deployment
```

`railway logs --deployment` streams and does not exit on its own. Pipe it (`| head -50`) so it
terminates.

Filter noise from Python services: `railway logs --deployment | grep -v httpx`.

---

## What a deployable folder looks like

Railway builds with Nixpacks, which infers the stack from the files present. It needs to know
two things: how to install, and how to start.

**Python (the usual default):**

```
my-api/
├── app.py               # or main.py
├── requirements.txt     # required - this is what marks it as Python
├── Procfile             # required - the start command
├── runtime.txt          # optional but recommended: python-3.11
└── .railwayignore       # keep the upload small
```

`Procfile` for a web service:
```
web: uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}
```

`Procfile` for a worker with no HTTP surface:
```
worker: python app.py
```

**Node:**
```
my-app/
├── package.json         # "start" script is the start command
├── package-lock.json
└── .railwayignore
```

**Anything else:** add a `Dockerfile` and Railway uses it instead of Nixpacks.

**`.railwayignore`** - same syntax as `.gitignore`. At minimum:
```
.venv/
venv/
__pycache__/
node_modules/
*.csv
*.db
.env
```

### Two rules that cause most first-deploy failures

**Bind to `0.0.0.0` and the `PORT` env var.** Railway assigns the port. A server on `127.0.0.1`
or a hardcoded port builds fine and then 502s forever.

```python
port = int(os.environ.get("PORT", 8080))
uvicorn.run(app, host="0.0.0.0", port=port)
```

**Never let `.venv` upload.** Nixpacks finds it and derives a start command from it, and the
service boots into the wrong thing. Put `.venv/` in `.railwayignore`.

---

## Gotchas that have actually bitten us

**The 413 "payload too large" gotcha.** `railway up` uploads the current directory - but if a
*parent* directory is linked to a Railway project, the CLI may index the whole parent tree. Deploying
from inside a big monorepo (several GB) fails with a 413. Fix: deploy from an
isolated copy containing only what the service needs.

```bash
D=/tmp/my-api-deploy && rm -rf $D && mkdir -p $D
cp path/to/my-api/{*.py,requirements.txt,Procfile,.railwayignore} $D/
cd $D
export RAILWAY_TOKEN=<token>
railway up --detach --service my-api
```

This is why a deploy command should document a `/tmp` staging dir. If a deploy suddenly 413s,
this is why.

**`--detach` in agent contexts.** Without it the CLI attaches to the log stream and blocks until
you interrupt it. Always pass `--detach` when deploying non-interactively.

**A deploy returning a build-log URL is not a successful deploy.** It means the build *started*.
Check `railway deployment list` for `SUCCESS` before telling anyone it shipped.

**Deploys take 2-4 minutes.** If a service exposes a version or `/health` endpoint, bump it and
poll that rather than guessing when the new code is live.

**`railway whoami` will fail here.** It is an account-level query and project tokens are not
account-scoped. Use `railway status` to confirm what you are pointed at.

**Python version.** Railway defaults to a recent Python. If code uses `str | None` syntax and
targets an older runtime, either pin `runtime.txt` to `python-3.11` or add
`from __future__ import annotations`.

---

## Volumes, crons, and workers

**Persistent disk** - a service's filesystem resets on every deploy. Anything that must survive
needs a volume, attached in the Railway dashboard and mounted at a path like `/data`. Then point
the app at it with an env var (`DATA_DIR=/data`).

**Cron** - set a schedule on the service in the dashboard (Settings > Cron Schedule) using
standard cron syntax. The service runs, then exits. A cron service should not have a domain and
its start command should be a script that terminates, not a server.

**Multiple services in one project** - `railway add` creates another, and `--service <name>`
targets it. Services in a project share a private network and can reference each other's
variables.

---

## Guardrails

- **Do not delete projects or services** without asking first. Deletion is irreversible and takes
  the volumes with it. This skill's helper deliberately has no delete command.
- **Do not touch projects you were not asked to touch.** The workspace token can see every
  project in the workspace. Read is fine; deploy only where asked.
- **Deploying is not the same as authorizing what the code does.** A service that writes to
  Instantly, Lemlist, a CRM or a database is an outward-facing system. Shipping one needs the
  explicit OK of whoever owns that system first.
- **Credentials go in Railway variables, not in the repo.** If a `.env` with real keys is about to
  be uploaded, stop and move it to `railway variables --set` instead.

---

## Credentials

`railway_helper.py` reads `RAILWAY_WORKSPACE_TOKEN` (required) and `RAILWAY_WORKSPACE_ID`
(optional) through `gtm.cred(...)`: environment first, then `~/.magna-gtm-config`, then the
`api_keys` table. Nothing is hardcoded in the helper and nothing belongs in the repo.

A workspace token cannot answer account-level queries (`me`, `apiTokens`). Seeing
`Not Authorized` on those is correct behavior, not a broken token.

**To create, rotate or revoke:** https://railway.com/account/tokens. Create the token **with the
workspace set** to the one you deploy into (leaving the workspace blank makes an account-wide
token, which is broader than this skill needs), then store it with
`python3 gtm.py set-key RAILWAY_WORKSPACE_TOKEN`. If `new` fails asking for a workspace, copy the
workspace id from the Railway dashboard URL and store it as `RAILWAY_WORKSPACE_ID`.

Project tokens minted by `railway_helper.py new` / `token` are per-project and appear under that
project's Settings > Tokens in the dashboard.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| CLI: `Unauthorized` | workspace token given to the CLI | mint a project token: `railway_helper.py token <project>` |
| `413` on `railway up` | parent tree being indexed | deploy from an isolated `/tmp` copy |
| Build SUCCESS, URL 502s | not bound to `0.0.0.0:$PORT` | fix the bind, redeploy |
| Start command is nonsense | `.venv` got uploaded | add `.venv/` to `.railwayignore`, redeploy |
| `railway whoami` fails | account-level query | use `railway status` |
| `Not Authorized` from the helper on `me` | expected for workspace tokens | ignore; use `projects` |
| Deploy succeeded, old code running | looking too early | `railway deployment list`, wait for `SUCCESS` |
| Variables missing after a move | vars live on the service, not in code | re-set them on the new service |

---

## Helper reference

```bash
python3 railway_helper.py whoami              # verify the token, count projects
python3 railway_helper.py projects            # all projects in the workspace + services
python3 railway_helper.py services <project>  # service + environment ids
python3 railway_helper.py new <name>          # create project, mint deploy token
python3 railway_helper.py token <project>     # mint a deploy token for an existing project
```

Project names resolve by exact id, exact name, then unique case-insensitive partial match.

---

## Railway's own agent skills

Railway ships official CLI-generated skills covering the full command surface:

```bash
railway setup agent -y      # installs Railway skills + MCP server
railway skills              # skills only
```

Those are the generic Railway reference. **This** skill is the layer on top: the credential, the
workspace pinning, and the failure modes above. If both are installed, this one
wins on anything about credentials or which workspace to deploy into.
