"""OPTIONAL: author an icp.json headlessly with Claude from research notes.

In-session authoring by Claude (see SKILL.md Step 2) is higher quality — use this only
when you need a hands-off run. Fetches the domain's site text, combines it with any
research notes you pass, and asks Claude to emit a full icp.json (matrix + airk blocks).

    python3 generate_icp.py --domain acme.com [--research notes.txt] [--example good_icp.json] [--out icp.json]

Needs ANTHROPIC_API_KEY. Then: python3 build.py icp.json
"""
from __future__ import annotations

import os
import sys
import json
import ssl
import argparse
import subprocess
import urllib.request
import urllib.error

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icp_schema.json")


def _fetch_site(domain: str) -> str:
    url = domain if domain.startswith("http") else f"https://{domain}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", "replace")
    except (ssl.SSLError, urllib.error.URLError, urllib.error.HTTPError):
        out = subprocess.run(["curl", "-sL", "-A", "Mozilla/5.0", url],
                             capture_output=True, text=True, timeout=45)
        raw = out.stdout
    import re
    raw = re.sub(r"<script.*?</script>", " ", raw, flags=re.S)
    raw = re.sub(r"<style.*?</style>", " ", raw, flags=re.S)
    txt = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", txt).strip()[:12000]


PROMPT = """You are a senior B2B ICP strategist. From the research below, produce a COMPLETE \
icp.json for the ICP → TAM Mapper skill. Return ONLY valid JSON, no prose, no code fences.

It must match this JSON schema:
```
%s
```

%s

Rules:
- The ICP is WHO THE COMPANY SHOULD SELL TO, not what they are. Infer the real buyer.
- `matrix` cells must be rich, specific, sourced ("SOURCE: Website research / Market analysis"). \
No thin one-liners. Bullets use \\n, paragraphs \\n\\n. Signal scoring max_points must sum to 100. \
Persona challenges and benefits must mirror 1:1.
- `airk.icp_type`: use "hybrid" when the ICP is a sub-segment inside a broad industry (industry + \
keyword gate); "signal_defined" when there is no clean industry; "firmographic" only when a clean \
industry fully defines it.
- `airk` geographies/industries must use real AI Ark values (full country names; LinkedIn-style \
industry strings). Seniorities are lowercase enums. Personas never include bare "Founder" as a title.

=== COMPANY ===
Domain: %s

=== SITE TEXT ===
%s

=== EXTRA RESEARCH NOTES ===
%s
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True)
    ap.add_argument("--research", help="path to a text file of extra research notes")
    ap.add_argument("--example", help="optional: a finished icp.json you trust, used as the quality bar")
    ap.add_argument("--out", default="icp.json")
    args = ap.parse_args()

    if not ANTHROPIC_API_KEY:
        sys.exit("ANTHROPIC_API_KEY not set — required for generate_icp.py")

    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    schema = open(SCHEMA_PATH).read()
    if args.example:
        example = ("Follow this worked example's structure and depth EXACTLY (it is the quality bar):\n"
                   "```\n" + open(args.example).read() + "\n```\n")
    else:
        example = ""
    site = _fetch_site(args.domain)
    notes = open(args.research).read()[:8000] if args.research else "(none)"

    print(f"Researching {args.domain} → drafting icp.json with {ANTHROPIC_MODEL}…")
    resp = client.messages.create(
        model=ANTHROPIC_MODEL, max_tokens=16000,
        messages=[{"role": "user",
                   "content": PROMPT % (schema, example, args.domain, site, notes)}],
    )
    out = resp.content[0].text.strip()
    import re
    out = re.sub(r"^```(?:json)?|```$", "", out, flags=re.M).strip()
    data = json.loads(out)  # validate it parses
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ wrote {args.out} — now run: python3 build.py {args.out}")


if __name__ == "__main__":
    main()
