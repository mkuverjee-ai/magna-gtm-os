#!/usr/bin/env python3
"""
Railway helper: workspace-level operations against the Railway Public API.

Why this exists: the Railway CLI does NOT accept workspace-scoped API tokens
(railwayapp/cli issue #845), but the GraphQL API does. So workspace-level work
(create a project, mint a deploy token, list projects) happens here, and the CLI
handles the actual deploy using the project token this script hands you.

Dependency-free (stdlib only). Python 3.9+.

Credentials (never hardcoded):
  RAILWAY_WORKSPACE_TOKEN  required. A workspace-scoped token for YOUR Railway
                           workspace (railway.com/account/tokens, workspace set).
  RAILWAY_WORKSPACE_ID     optional. The workspace new projects are created in.
                           Needed by `new` if Railway cannot infer it from the token.
Both are read via gtm.cred(...): environment -> ~/.magna-gtm-config -> the
api_keys table. Set them once with `python3 gtm.py set-key NAME` (value on stdin).

Usage:
  python3 railway_helper.py projects
  python3 railway_helper.py new <project-name>
  python3 railway_helper.py token <project-name-or-id>
  python3 railway_helper.py services <project-name-or-id>
  python3 railway_helper.py whoami
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API = "https://backboard.railway.com/graphql/v2"

WORKSPACE_LABEL = "your Railway workspace"


def _cred(name: str) -> str:
    """Environment first, then gtm.cred() from the repo root if it is available."""
    val = os.environ.get(name, "").strip()
    if val:
        return val
    repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    if os.path.exists(os.path.join(repo, "gtm.py")):
        sys.path.insert(0, repo)
        try:
            import gtm
            try:
                val = gtm.cred(name, required=False)
            except TypeError:
                val = gtm.cred(name)
        except SystemExit:
            val = ""
        except Exception:
            val = ""
    return (val or "").strip()


def _token() -> str:
    tok = _cred("RAILWAY_WORKSPACE_TOKEN")
    if not tok:
        sys.exit(
            "No Railway workspace token. Create a workspace-scoped token at "
            "https://railway.com/account/tokens (set the workspace), then store it with:\n"
            "  python3 gtm.py set-key RAILWAY_WORKSPACE_TOKEN   (paste the value on stdin)"
        )
    return tok


def _workspace_id() -> str:
    return _cred("RAILWAY_WORKSPACE_ID")


def gql(query: str, variables: dict | None = None) -> dict:
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": "Bearer " + _token(),
            "Content-Type": "application/json",
            # Railway sits behind Cloudflare, which 403s urllib's default UA.
            "User-Agent": "railway-helper/1.0",
        },
    )
    try:
        raw = urllib.request.urlopen(req, timeout=60).read().decode()
    except urllib.error.HTTPError as exc:
        sys.exit("HTTP %s from Railway: %s" % (exc.code, exc.read().decode()[:400]))
    out = json.loads(raw)
    if out.get("errors"):
        msgs = "; ".join(e.get("message", "?") for e in out["errors"])
        if "Not Authorized" in msgs:
            msgs += (
                "\n\nNote: a workspace token cannot answer account-level queries "
                "(me, apiTokens). That is expected and not a broken token."
            )
        sys.exit("Railway API error: " + msgs)
    return out["data"]


PROJECTS_Q = """
query {
  projects {
    edges { node {
      id name createdAt
      environments { edges { node { id name } } }
      services { edges { node { id name } } }
    } }
  }
}
"""


def list_projects() -> list[dict]:
    data = gql(PROJECTS_Q)
    return [e["node"] for e in data["projects"]["edges"]]


def resolve(ref: str) -> dict:
    """Find a project by exact id, exact name, then case-insensitive name."""
    projects = list_projects()
    for p in projects:
        if p["id"] == ref or p["name"] == ref:
            return p
    matches = [p for p in projects if p["name"].lower() == ref.lower()]
    if len(matches) == 1:
        return matches[0]
    partial = [p for p in projects if ref.lower() in p["name"].lower()]
    if len(partial) == 1:
        return partial[0]
    if partial:
        sys.exit(
            "Ambiguous project '%s'. Matches: %s"
            % (ref, ", ".join(p["name"] for p in partial))
        )
    sys.exit(
        "No project '%s' in %s. Run `projects` to list them."
        % (ref, WORKSPACE_LABEL)
    )


def prod_env(project: dict) -> dict:
    envs = [e["node"] for e in project["environments"]["edges"]]
    for e in envs:
        if e["name"] == "production":
            return e
    if not envs:
        sys.exit("Project '%s' has no environments." % project["name"])
    return envs[0]


def mint_project_token(project: dict, name: str = "skill-deploy") -> str:
    env = prod_env(project)
    data = gql(
        "mutation($input: ProjectTokenCreateInput!){ projectTokenCreate(input:$input) }",
        {
            "input": {
                "name": name,
                "projectId": project["id"],
                "environmentId": env["id"],
            }
        },
    )
    return data["projectTokenCreate"]


def cmd_whoami() -> None:
    projects = list_projects()
    wid = _workspace_id()
    print("Workspace: %s" % (wid or "(RAILWAY_WORKSPACE_ID not set; inferred from the token)"))
    print("Token is valid. %d project(s) visible." % len(projects))
    print("Scope: whatever workspace the token was created for.")


def cmd_projects() -> None:
    projects = list_projects()
    if not projects:
        print("No projects in %s yet." % WORKSPACE_LABEL)
        return
    print("Projects in %s:\n" % WORKSPACE_LABEL)
    for p in sorted(projects, key=lambda x: x["name"].lower()):
        svcs = [s["node"]["name"] for s in p["services"]["edges"]]
        print("  %-38s %s" % (p["name"], p["id"]))
        if svcs:
            print("      services: %s" % ", ".join(svcs))


def cmd_services(ref: str) -> None:
    p = resolve(ref)
    print("Project: %s (%s)" % (p["name"], p["id"]))
    for e in p["environments"]["edges"]:
        print("  env %-12s %s" % (e["node"]["name"], e["node"]["id"]))
    svcs = [s["node"] for s in p["services"]["edges"]]
    if not svcs:
        print("  (no services yet - `railway up` creates one)")
    for s in svcs:
        print("  service %-24s %s" % (s["name"], s["id"]))


def cmd_new(name: str) -> None:
    for p in list_projects():
        if p["name"].lower() == name.lower():
            sys.exit(
                "A project named '%s' already exists (%s). Use `token %s` to get a "
                "deploy token for it instead." % (p["name"], p["id"], p["name"])
            )
    inp = {"name": name}
    wid = _workspace_id()
    if wid:
        inp["workspaceId"] = wid
    data = gql(
        "mutation($input: ProjectCreateInput!){ projectCreate(input:$input){ "
        "id name environments{edges{node{id name}}} } }",
        {"input": inp},
    )
    project = data["projectCreate"]
    project.setdefault("services", {"edges": []})
    token = mint_project_token(project)
    env = prod_env(project)
    print("Created project '%s' in %s" % (project["name"], WORKSPACE_LABEL))
    print("  project id:     %s" % project["id"])
    print("  environment:    %s (%s)" % (env["name"], env["id"]))
    print("\nDeploy token (scoped to this project + environment):\n")
    print("  export RAILWAY_TOKEN=%s" % token)
    print("\nThen, from the folder you want to deploy:\n")
    print("  railway up --detach")


def cmd_token(ref: str) -> None:
    p = resolve(ref)
    token = mint_project_token(p)
    env = prod_env(p)
    print("Project: %s (%s), env %s" % (p["name"], p["id"], env["name"]))
    print("\n  export RAILWAY_TOKEN=%s\n" % token)


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return
    cmd, rest = args[0], args[1:]
    if cmd == "whoami":
        cmd_whoami()
    elif cmd in ("projects", "list", "ls"):
        cmd_projects()
    elif cmd == "new":
        if not rest:
            sys.exit("Usage: new <project-name>")
        cmd_new(rest[0])
    elif cmd == "token":
        if not rest:
            sys.exit("Usage: token <project-name-or-id>")
        cmd_token(rest[0])
    elif cmd == "services":
        if not rest:
            sys.exit("Usage: services <project-name-or-id>")
        cmd_services(rest[0])
    else:
        sys.exit("Unknown command '%s'. Run --help." % cmd)


if __name__ == "__main__":
    main()
