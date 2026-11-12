# ICP Matrix XLSX Generator

Full Python code template for generating a styled ICP matrix workbook.

## Dependencies

```bash
pip install openpyxl
```

## Full Generator Script

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import csv
import os

# ============================================================
# CONFIGURATION — Update these for each matrix
# ============================================================

CLIENT_NAME = "CompanyName"  # PascalCase, used in filenames
OUTPUT_DIR = "plays/<play-slug>/research"  # or "company" for the company-wide matrix

# ============================================================
# STYLES
# ============================================================

header_font = Font(name='Calibri', bold=True, color='FFFFFF', size=11)
header_fill = PatternFill(start_color='1F4E79', end_color='1F4E79', fill_type='solid')
cell_font = Font(name='Calibri', size=11)
cell_alignment = Alignment(wrap_text=True, vertical='top')
header_alignment = Alignment(wrap_text=True, vertical='center', horizontal='center')
thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

def style_header(cell):
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = header_alignment
    cell.border = thin_border

def style_cell(cell):
    cell.font = cell_font
    cell.alignment = cell_alignment
    cell.border = thin_border

def auto_width(ws, min_width=20, max_width=80):
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = min_width
        for cell in col:
            if cell.value:
                lines = str(cell.value).split('\n')
                longest_line = max(len(line) for line in lines)
                max_len = max(max_len, min(longest_line + 2, max_width))
        ws.column_dimensions[col_letter].width = max_len

# ============================================================
# SHEET BUILDERS
# ============================================================

def build_account_level(wb, data):
    """
    data = list of dicts with keys:
        category, qualified, prioritization
    """
    ws = wb.active
    ws.title = "Account Level"
    headers = ["Lead Score Category", "Qualified", "Prioritization"]

    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        style_header(cell)

    for row_idx, row_data in enumerate(data, 2):
        for col_idx, key in enumerate(["category", "qualified", "prioritization"], 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=row_data.get(key, ""))
            style_cell(cell)

    auto_width(ws)
    return ws


def build_prospect_level(wb, data):
    """
    data = list of dicts with keys:
        category, qualified, prioritization
    """
    ws = wb.create_sheet("Prospect Level")
    headers = ["Lead Score Category", "Qualified", "Prioritization"]

    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        style_header(cell)

    for row_idx, row_data in enumerate(data, 2):
        for col_idx, key in enumerate(["category", "qualified", "prioritization"], 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=row_data.get(key, ""))
            style_cell(cell)

    auto_width(ws)
    return ws


def build_persona_matrix(wb, data):
    """
    data = list of dicts with keys:
        persona, level, kpis, challenges, intent_signals, benefits
    """
    ws = wb.create_sheet("Persona Matrix")
    headers = ["Persona", "Level", "KPIs", "Related Challenges", "Intent Signals", "Related Benefits"]

    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        style_header(cell)

    keys = ["persona", "level", "kpis", "challenges", "intent_signals", "benefits"]
    for row_idx, row_data in enumerate(data, 2):
        for col_idx, key in enumerate(keys, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=row_data.get(key, ""))
            style_cell(cell)

    auto_width(ws)
    return ws


def build_signal_scoring(wb, data, tier_thresholds, note=""):
    """
    data = list of dicts with keys:
        category, criteria, points, max_points, notes

    tier_thresholds = list of dicts with keys:
        tier, points, treatment
    """
    ws = wb.create_sheet("Signal Scoring")

    # Title row
    title_cell = ws.cell(row=1, column=1, value=f"{CLIENT_NAME.upper()} ACCOUNT SCORING MODEL (100 Points Max)")
    title_cell.font = Font(name='Calibri', bold=True, size=14)

    # Headers at row 3
    headers = ["Signal Category", "Criteria", "Points", "Max Points", "Notes"]
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_idx, value=header)
        style_header(cell)

    # Scoring rows
    current_row = 4
    for row_data in data:
        for col_idx, key in enumerate(["category", "criteria", "points", "max_points", "notes"], 1):
            cell = ws.cell(row=current_row, column=col_idx, value=row_data.get(key, ""))
            style_cell(cell)
        current_row += 1

    # Blank row
    current_row += 1

    # Tier thresholds header
    ws.cell(row=current_row, column=1, value="TIER THRESHOLDS").font = Font(bold=True, size=12)
    current_row += 1

    for tier_data in tier_thresholds:
        ws.cell(row=current_row, column=1, value=tier_data.get("tier", ""))
        ws.cell(row=current_row, column=2, value=tier_data.get("points", ""))
        ws.cell(row=current_row, column=3, value=tier_data.get("treatment", ""))
        for col_idx in range(1, 6):
            style_cell(ws.cell(row=current_row, column=col_idx))
        current_row += 1

    # Note
    if note:
        current_row += 1
        ws.cell(row=current_row, column=1, value=f"NOTE: {note}")

    auto_width(ws)
    return ws


def build_case_study_reference(wb, case_studies, dream_clients, excluded, key_signal_header="Key Signal"):
    """
    case_studies, dream_clients, excluded = lists of dicts with keys:
        company, industry, icp_segment, key_signal, key_insight, source
    """
    ws = wb.create_sheet("Case Study Reference")

    # Title
    title_cell = ws.cell(row=1, column=1, value=f"{CLIENT_NAME.upper()} CASE STUDY COMPANIES - ICP VALIDATION")
    title_cell.font = Font(name='Calibri', bold=True, size=14)

    # Headers at row 3
    headers = ["Company", "Industry", "ICP Segment", key_signal_header, "Key Insight", "Source"]
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col_idx, value=header)
        style_header(cell)

    current_row = 4

    # Case study companies
    for row_data in case_studies:
        for col_idx, key in enumerate(["company", "industry", "icp_segment", "key_signal", "key_insight", "source"], 1):
            cell = ws.cell(row=current_row, column=col_idx, value=row_data.get(key, ""))
            style_cell(cell)
        current_row += 1

    # Dream clients section
    current_row += 1
    ws.cell(row=current_row, column=1, value="DREAM CLIENTS (from target domains):").font = Font(bold=True, size=11)
    current_row += 1

    for row_data in dream_clients:
        for col_idx, key in enumerate(["company", "industry", "icp_segment", "key_signal", "key_insight", "source"], 1):
            cell = ws.cell(row=current_row, column=col_idx, value=row_data.get(key, ""))
            style_cell(cell)
        current_row += 1

    # Excluded section
    current_row += 1
    ws.cell(row=current_row, column=1, value="EXCLUDED COMPANIES (with rationale):").font = Font(bold=True, size=11)
    current_row += 1

    for row_data in excluded:
        for col_idx, key in enumerate(["company", "industry", "icp_segment", "key_signal", "key_insight", "source"], 1):
            cell = ws.cell(row=current_row, column=col_idx, value=row_data.get(key, ""))
            style_cell(cell)
        current_row += 1

    auto_width(ws)
    return ws

# ============================================================
# CSV EXPORT
# ============================================================

def export_sheets_to_csv(wb, output_dir, client_name):
    """Export each sheet as a separate CSV file."""
    for ws in wb.worksheets:
        sheet_name = ws.title.replace(" ", "_")
        csv_path = os.path.join(output_dir, f"{client_name}_ICP_Matrix_{sheet_name}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for row in ws.iter_rows(values_only=True):
                writer.writerow(row)
        print(f"Exported: {csv_path}")

# ============================================================
# MAIN — Fill in the matrix data below
# ============================================================

if __name__ == "__main__":
    wb = openpyxl.Workbook()

    # --- FILL THESE WITH YOUR MATRIX DATA ---

    account_level_data = [
        # {"category": "LOCATION / GEOGRAPHY", "qualified": "...", "prioritization": "..."},
        # ...
    ]

    prospect_level_data = [
        # {"category": "SENIORITY", "qualified": "...", "prioritization": "..."},
        # ...
    ]

    persona_data = [
        # {"persona": "...", "level": "...", "kpis": "...", "challenges": "...", "intent_signals": "...", "benefits": "..."},
        # ...
    ]

    scoring_data = [
        # {"category": "KEY SIGNAL", "criteria": "...", "points": 40, "max_points": 40, "notes": "..."},
        # ...
    ]

    tier_thresholds = [
        {"tier": "Tier 1 (High Touch)", "points": "70+ points", "treatment": "ABM, personalized outreach, multi-thread"},
        {"tier": "Tier 2 (Multi-Channel)", "points": "45-69 points", "treatment": "Multi-channel sequence, case-study-led outreach"},
        {"tier": "Tier 3 (Nurture)", "points": "<45 points", "treatment": "Nurture, re-evaluate quarterly"},
    ]

    case_studies = []
    dream_clients = []
    excluded_companies = []

    # --- BUILD WORKBOOK ---

    build_account_level(wb, account_level_data)
    build_prospect_level(wb, prospect_level_data)
    build_persona_matrix(wb, persona_data)
    build_signal_scoring(wb, scoring_data, tier_thresholds,
                         note="Scoring thresholds need calibration against won/lost deals")
    build_case_study_reference(wb, case_studies, dream_clients, excluded_companies,
                               key_signal_header="Key Signal")

    # --- SAVE ---

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    xlsx_path = os.path.join(OUTPUT_DIR, f"{CLIENT_NAME}_ICP_Matrix.xlsx")
    wb.save(xlsx_path)
    print(f"Saved: {xlsx_path}")

    export_sheets_to_csv(wb, OUTPUT_DIR, CLIENT_NAME)
    print("Done!")
```

## Usage

1. Copy this script
2. Update `CLIENT_NAME` and `OUTPUT_DIR`
3. Fill in the data arrays with the content from Phases 1-7
4. Run: `python generate_icp_matrix.py`
5. Verify the `.xlsx` opens correctly and all 5 sheets are populated
