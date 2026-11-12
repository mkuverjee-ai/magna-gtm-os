#!/usr/bin/env python3
"""
Floqer Public API client — thin, dependency-free wrapper for the common build loop.

Usage:
    python3 gtm.py set-key FLOQER_API_KEY   # once (or export it, or skills/floqer/.env)
    python3 floqer_client.py whoami
    python3 floqer_client.py workflows
    python3 floqer_client.py overview <workflow_id>
    python3 floqer_client.py inputs <workflow_id> [sheet_id]
    python3 floqer_client.py rows <workflow_id> [sheet_id]
    python3 floqer_client.py sources

Or import Floqer and drive the full build loop programmatically.
Concepts + endpoint reference: see SKILL.md and reference/concepts.txt.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://api.floqer.com/api/v1"


def _load_key() -> str:
    key = os.environ.get("FLOQER_API_KEY")
    if not key:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path) as fh:
                for line in fh:
                    if line.strip().startswith("FLOQER_API_KEY="):
                        key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                        break
    if not key:
        repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
        if os.path.exists(os.path.join(repo, "gtm.py")):
            sys.path.insert(0, repo)
            try:
                import gtm
                key = gtm.cred("FLOQER_API_KEY", required=False)
            except Exception:
                key = None
    if not key:
        sys.exit("FLOQER_API_KEY not set. Floqer is optional; if you have a key, "
                 "add it with: python3 gtm.py set-key FLOQER_API_KEY")
    return key


class Floqer:
    def __init__(self, api_key: str | None = None):
        self.key = api_key or _load_key()

    def _req(self, method: str, path: str, body: dict | list | None = None, _retries: int = 3):
        url = f"{BASE}{path}"
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": f"Bearer {self.key}"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            payload = e.read().decode()
            # Honor rate-limit backoff
            if e.code == 429 and _retries > 0:
                try:
                    wait = json.loads(payload).get("retryAfter", 5)
                except Exception:
                    wait = 5
                time.sleep(wait + 1)
                return self._req(method, path, body, _retries - 1)
            raise RuntimeError(f"HTTP {e.code} {method} {path}: {payload}") from None

    # --- identity ---
    def whoami(self):
        return self._req("GET", "/user/")

    def get_knowledge(self):
        return self._req("GET", "/user/knowledge")

    def set_knowledge(self, content: str):
        return self._req("PUT", "/user/knowledge", {"content": content})

    # --- workflows / sheets ---
    def create_workflow(self, name: str):
        return self._req("POST", "/workflows/", {"name": name})

    def list_workflows(self):
        return self._req("GET", "/workflows/")

    def overview(self, workflow_id: str):
        return self._req("GET", f"/workflows/{workflow_id}")

    def delete_workflow(self, workflow_id: str):
        return self._req("DELETE", f"/workflows/{workflow_id}")

    def create_sheet(self, workflow_id: str, name: str, **opts):
        return self._req("POST", f"/workflows/{workflow_id}/sheets", {"name": name, **opts})

    # --- inputs (sheet_id defaults to workflow_id = main sheet) ---
    def list_inputs(self, workflow_id: str, sheet_id: str | None = None):
        sid = sheet_id or workflow_id
        return self._req("GET", f"/workflows/{workflow_id}/sheets/{sid}/inputs")

    def add_inputs(self, workflow_id: str, inputs: list, sheet_id: str | None = None):
        sid = sheet_id or workflow_id
        return self._req("POST", f"/workflows/{workflow_id}/sheets/{sid}/inputs", inputs)

    # --- actions ---
    def add_action(self, workflow_id: str, action_id: str, sheet_id: str | None = None, **opts):
        sid = sheet_id or workflow_id
        return self._req("POST", f"/workflows/{workflow_id}/sheets/{sid}/actions/add",
                         {"action_id": action_id, **opts})

    def configure_action(self, workflow_id: str, aid: str, body: dict, sheet_id: str | None = None):
        sid = sheet_id or workflow_id
        return self._req("PATCH", f"/workflows/{workflow_id}/sheets/{sid}/actions/{aid}", body)

    def action_graph(self, workflow_id: str, sheet_id: str | None = None):
        sid = sheet_id or workflow_id
        return self._req("GET", f"/workflows/{workflow_id}/sheets/{sid}/actions/graph")

    def field_options(self, workflow_id: str, aid: str, field_name: str,
                      context: dict | None = None, sheet_id: str | None = None):
        sid = sheet_id or workflow_id
        return self._req("POST",
                         f"/workflows/{workflow_id}/sheets/{sid}/actions/{aid}/options/{field_name}",
                         {"context": context} if context else {})

    # --- rows / running ---
    def add_rows(self, workflow_id: str, rows: list, run_after_add: str = "none",
                 sheet_id: str | None = None):
        sid = sheet_id or workflow_id
        return self._req("POST", f"/workflows/{workflow_id}/sheets/{sid}/rows",
                         {"rows": rows, "run_after_add": run_after_add})

    def run(self, workflow_id: str, row_ids: list | None = None, first_10: bool = False,
            sheet_id: str | None = None):
        sid = sheet_id or workflow_id
        body = {"first_10": True} if first_10 else {"row_ids": row_ids or []}
        return self._req("POST", f"/workflows/{workflow_id}/sheets/{sid}/run", body)

    def run_all(self, workflow_id: str, sheet_id: str | None = None):
        sid = sheet_id or workflow_id
        return self._req("POST", f"/workflows/{workflow_id}/sheets/{sid}/run-all", {})

    def list_rows(self, workflow_id: str, sheet_id: str | None = None, **body):
        sid = sheet_id or workflow_id
        return self._req("POST", f"/workflows/{workflow_id}/sheets/{sid}/rows/list", body or {})

    def poll_rows(self, workflow_id: str, sheet_id: str | None = None,
                  interval: int = 5, max_wait: int = 600, **list_body):
        """Poll List Rows until every returned row settles (no queued/running cells)."""
        waited = 0
        while waited < max_wait:
            resp = self.list_rows(workflow_id, sheet_id, **list_body)
            rows = resp.get("data", {}).get("rows", resp.get("data", []))
            statuses = [r.get("row_status") for r in rows] if isinstance(rows, list) else []
            if statuses and all(s in ("complete", "has_failures") for s in statuses):
                return resp
            time.sleep(interval)
            waited += interval
        return self.list_rows(workflow_id, sheet_id, **list_body)

    # --- sources ---
    def list_sources(self):
        return self._req("GET", "/sources/")

    def preview_source(self, source_id: str, body: dict):
        return self._req("POST", f"/sources/{source_id}/preview", body)

    def create_source(self, source_id: str, body: dict):
        return self._req("POST", f"/sources/{source_id}", body)

    def source_options(self, source_id: str, field_name: str, context: dict | None = None):
        return self._req("POST", f"/sources/{source_id}/options/{field_name}",
                         {"context": context} if context else {})

    def source_data(self, source_instance_id: str, page_no: int = 1, page_size: int = 20):
        return self._req("GET", f"/sources/{source_instance_id}/data?page_no={page_no}&page_size={page_size}")

    def sync_source(self, source_instance_id: str, workflow_id: str, field_mapping: dict, **opts):
        return self._req("POST", f"/sources/{source_instance_id}/sync",
                         {"workflow_id": workflow_id, "field_mapping": field_mapping, **opts})


def _cli():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    f = Floqer()
    cmd, args = sys.argv[1], sys.argv[2:]
    dispatch = {
        "whoami": lambda: f.whoami(),
        "workflows": lambda: f.list_workflows(),
        "overview": lambda: f.overview(args[0]),
        "inputs": lambda: f.list_inputs(args[0], args[1] if len(args) > 1 else None),
        "rows": lambda: f.list_rows(args[0], args[1] if len(args) > 1 else None, page_size=50),
        "sources": lambda: f.list_sources(),
    }
    if cmd not in dispatch:
        sys.exit(f"unknown command '{cmd}'. See --help.\n{__doc__}")
    print(json.dumps(dispatch[cmd](), indent=2))


if __name__ == "__main__":
    _cli()
