# icp-tam-mapper

Give it a company, get back an **ICP Matrix (XLSX)** + a **live AI Ark TAM → SAM → SOM breakdown**.

One repeatable pipeline for the manual work of: research a company → build a 5-sheet ICP matrix →
translate the ICP into AI Ark search filters → run live market-size and buyer-persona counts.

```
domain ──► research ──► icp.json ──► build.py ──► ┌ {Company}_ICP_Matrix.xlsx  (+ CSVs)
                                                   ├ {company}-airk-filters.json (paste-ready)
                                                   └ {Company}_TAM_Breakdown.md  (live counts)
```

## Quick start

```bash
pip install -r requirements.txt
python3 gtm.py set-key AI_ARK_API_KEY        # once, from the repo root

# 1) Author an icp.json that conforms to icp_schema.json (see SKILL.md Step 2)
# 2) Build everything (ICP matrix XLSX + AI Ark filters + live TAM/SAM/SOM)
python3 build.py plays/<play-slug>/research/icp.json ./out
```

Optional headless authoring (drafts the icp.json with Claude):
```bash
python3 generate_icp.py --domain acme.com --out my_icp.json && python3 build.py my_icp.json
```

## How it works

| Stage | File | Notes |
|-------|------|-------|
| ICP matrix → XLSX | `icp_matrix.py` | 5 sheets (Calibri, dark-blue headers) + per-sheet CSVs |
| ICP → AI Ark filters + counts | `airk.py` | Read-only `/companies` + `/people` search. TAM/SAM/SOM + personas. curl TLS fallback. |
| Orchestration | `build.py` | `icp.json` → all three outputs |
| Config / maps | `config.py` | Key lookup (env → `gtm.cred`), region→country + vertical→industry expansion |
| Input contract | `icp_schema.json` | `matrix` block (XLSX) + `airk` block (funnel) |

`icp_type` decides the AI Ark gate: `firmographic` (industry only), `signal_defined` (keyword only),
or `hybrid` (industry + keyword gate — the usual case for a sub-segment inside a broad industry, e.g.
executive search inside Staffing & Recruiting).

## Read-only

All AI Ark calls are count-only search requests. This tool never writes to AI Ark or any other
service. The Key Qualifying Signal + intent live outside AI Ark — the breakdown lists them under
"layer in Clay."

## Reference

- Full recipe + gotchas: [`SKILL.md`](./SKILL.md)
- AI Ark API reference: `skills/ai-ark/SKILL.md`
