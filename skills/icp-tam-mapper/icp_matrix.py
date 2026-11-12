"""ICP Matrix → styled 5-sheet Excel workbook (+ per-sheet CSVs).

Standard 5-sheet ICP Matrix format (same layout as skills/icp-matrix):
  1. Account Level      (8 dimensions)
  2. Prospect Level     (4 dimensions)
  3. Persona Matrix     (5-6 personas)
  4. Signal Scoring     (100-point model + tier thresholds)
  5. Case Study Reference (proof / dream clients / exclusions)

Input is the `matrix` block of an icp.json (see icp_schema.json).
"""
import os
import csv
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


def build_xlsx(matrix: dict, company_name: str, out_dir: str) -> str:
    wb = openpyxl.Workbook()

    header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell_align = Alignment(wrap_text=True, vertical="top")
    thin = Border(left=Side(style="thin"), right=Side(style="thin"),
                  top=Side(style="thin"), bottom=Side(style="thin"))

    def style_header(ws, row=1, cols=None):
        for col in range(1, (cols or ws.max_column) + 1):
            c = ws.cell(row=row, column=col)
            c.font, c.fill, c.alignment, c.border = header_font, header_fill, header_align, thin

    def style_cells(ws, start=2):
        for row in ws.iter_rows(min_row=start, max_row=ws.max_row, max_col=ws.max_column):
            for c in row:
                c.alignment, c.border = cell_align, thin

    def auto_width(ws, min_w=15, max_w=55):
        for col in ws.columns:
            letter = col[0].column_letter
            m = 0
            for c in col:
                if c.value:
                    m = max(m, max((len(l) for l in str(c.value).split("\n")), default=0))
            ws.column_dimensions[letter].width = min(max(m + 2, min_w), max_w)

    def fit(ws):
        ws.sheet_properties.pageSetUpPr = openpyxl.worksheet.properties.PageSetupProperties(fitToPage=True)
        ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
        ws.page_setup.orientation = "landscape"

    # Sheet 1 — Account Level
    ws1 = wb.active
    ws1.title = "Account Level"
    ws1.append(["Lead Score Category", "Qualified", "Prioritization"])
    style_header(ws1, cols=3)
    for r in matrix.get("account_level", []):
        ws1.append([r.get("category", ""), r.get("qualified", ""), r.get("prioritization", "")])
    style_cells(ws1); auto_width(ws1); fit(ws1)

    # Sheet 2 — Prospect Level
    ws2 = wb.create_sheet("Prospect Level")
    ws2.append(["Lead Score Category", "Qualified", "Prioritization"])
    style_header(ws2, cols=3)
    for r in matrix.get("prospect_level", []):
        ws2.append([r.get("category", ""), r.get("qualified", ""), r.get("prioritization", "")])
    style_cells(ws2); auto_width(ws2); fit(ws2)

    # Sheet 3 — Persona Matrix
    ws3 = wb.create_sheet("Persona Matrix")
    ws3.append(["Persona", "Level", "KPIs", "Related Challenges", "Intent Signals", "Related Benefits"])
    style_header(ws3, cols=6)
    for p in matrix.get("persona_matrix", []):
        ws3.append([p.get("persona", ""), p.get("level", ""), p.get("kpis", ""),
                    p.get("challenges", ""), p.get("intent_signals", ""), p.get("benefits", "")])
    style_cells(ws3); auto_width(ws3); fit(ws3)

    # Sheet 4 — Signal Scoring
    ws4 = wb.create_sheet("Signal Scoring")
    scoring = matrix.get("signal_scoring", {})
    if scoring.get("title_row"):
        ws4.append([scoring["title_row"], "", "", "", ""])
        ws4.cell(row=1, column=1).font = Font(name="Calibri", bold=True, size=12)
        ws4.append(["", "", "", "", ""])
    ws4.append(["Signal Category", "Criteria", "Points", "Max Points", "Notes"])
    style_header(ws4, row=ws4.max_row, cols=5)
    for cat in scoring.get("categories", []):
        if cat.get("category") == "SEPARATOR":
            ws4.append(["", "", "", "", ""]); continue
        ws4.append([cat.get("category", ""), cat.get("criteria", ""),
                    cat.get("points", ""), cat.get("max_points", ""), cat.get("notes", "")])
    ws4.append(["", "", "", "", ""])
    ws4.append(["TIER THRESHOLDS", "", "", "", ""])
    ws4.cell(row=ws4.max_row, column=1).font = Font(bold=True)
    for t in scoring.get("tier_thresholds", []):
        ws4.append([t.get("tier", ""), t.get("treatment", ""), "", t.get("points", ""), ""])
    ws4.append(["", "", "", "", ""])
    ws4.append(["NOTE: Scoring thresholds need calibration against won/lost deals", "", "", "", ""])
    style_cells(ws4); auto_width(ws4); fit(ws4)

    # Sheet 5 — Case Study Reference
    key_signal_name = matrix.get("key_signal_name", "Key Signal")
    ws5 = wb.create_sheet("Case Study Reference")
    ws5.append(["Company", "Industry", "ICP Segment", key_signal_name, "Key Insight", "Source"])
    style_header(ws5, cols=6)
    ref = matrix.get("case_study_reference", {})
    for section, color, key in [("— CASE STUDY / PROOF COMPANIES —", "1F4E79", "case_studies"),
                                ("— DREAM CLIENTS —", "1F4E79", "dream_clients"),
                                ("— EXCLUDED COMPANIES —", "CC0000", "excluded")]:
        rows = ref.get(key)
        if not rows:
            continue
        ws5.append([section, "", "", "", "", ""])
        ws5.cell(row=ws5.max_row, column=1).font = Font(bold=True, color=color)
        for r in rows:
            ws5.append([r.get("company", ""), r.get("industry", ""),
                        r.get("icp_segment", ""), r.get("key_signal", ""),
                        r.get("key_insight", ""), r.get("source", "")])
    style_cells(ws5); auto_width(ws5); fit(ws5)

    safe = (company_name.replace(" ", "_").replace("/", "-")
            .replace("(", "").replace(")", ""))
    os.makedirs(out_dir, exist_ok=True)
    xlsx_path = os.path.join(out_dir, f"{safe}_ICP_Matrix.xlsx")
    wb.save(xlsx_path)

    for ws in wb.worksheets:
        sheet = ws.title.replace(" ", "_")
        with open(os.path.join(out_dir, f"{safe}_ICP_Matrix_{sheet}.csv"), "w",
                  newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for row in ws.iter_rows(values_only=True):
                w.writerow(row)
    return xlsx_path
