"""Config + reference maps for the ICP → TAM Mapper skill.

Everything the skill needs to talk to AI Ark and to expand human-friendly ICP
language into AI Ark filter values lives here. The AI Ark key is read from the
AI_ARK_API_KEY environment variable, then gtm.cred() (~/.magna-gtm-config, then
the api_keys table). It is never baked into this file: a stale hard-coded key
silently spends a different account's credits.
"""
import os
import sys


def _ai_ark_key() -> str:
    key = os.environ.get("AI_ARK_API_KEY", "").strip()
    if key:
        return key
    repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    if os.path.exists(os.path.join(repo, "gtm.py")):
        sys.path.insert(0, repo)
        try:
            import gtm
            return (gtm.cred("AI_ARK_API_KEY", required=False) or "").strip()
        except Exception:
            return ""
    return ""


# ── AI Ark ────────────────────────────────────────────────────────────────────
AI_ARK_API_KEY = _ai_ark_key()
AI_ARK_BASE = "https://api.ai-ark.com/api/developer-portal/v1"
AI_ARK_UA = "Mozilla/5.0 (compatible; GTM-OS-TAM/1.0)"  # default urllib UA gets 403'd by the WAF

# Anthropic (only needed if you use generate_icp.py to build the ICP headlessly).
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ICP_MODEL", "claude-sonnet-4-6")

# ── Keyword sources (company keyword filter) ──────────────────────────────────
# AI Ark searches these three text sources when matching the "what they do" gate.
KEYWORD_SOURCES = [
    {"mode": "SMART", "source": "KEYWORD"},
    {"mode": "SMART", "source": "DESCRIPTION"},
    {"mode": "SMART", "source": "SEO"},
]

# ── Region → country expansion ────────────────────────────────────────────────
# Short region names an ICP might use, expanded to the full country names AI Ark
# location filters expect. Extend as needed.
REGION_EXPANSION = {
    "north america": ["United States", "Canada"],
    "united states": ["United States"],
    "usa": ["United States"],
    "us": ["United States"],
    "uk": ["United Kingdom"],
    "united kingdom": ["United Kingdom"],
    "western europe": ["United Kingdom", "Germany", "France", "Netherlands", "Ireland", "Sweden", "Switzerland"],
    "eu": ["Germany", "France", "Netherlands", "Ireland", "Sweden", "Spain", "Italy"],
    "dach": ["Germany", "Austria", "Switzerland"],
    "nordics": ["Sweden", "Norway", "Denmark", "Finland"],
    "benelux": ["Netherlands", "Belgium", "Luxembourg"],
    "gcc": ["United Arab Emirates", "Saudi Arabia", "Qatar", "Kuwait", "Bahrain", "Oman"],
    "mena": ["United Arab Emirates", "Saudi Arabia", "Egypt", "Qatar"],
    "uae": ["United Arab Emirates"],
    "middle east": ["United Arab Emirates", "Saudi Arabia", "Qatar"],
    "anz": ["Australia", "New Zealand"],
    "australia/nz": ["Australia", "New Zealand"],
    "apac": ["Singapore", "Australia", "India", "Japan"],
    "israel": ["Israel"],
    "canada": ["Canada"],
    "singapore": ["Singapore"],
}

# ── Vertical → AI Ark industry expansion ──────────────────────────────────────
# Human vertical names → the LinkedIn-style industry strings AI Ark recognizes.
INDUSTRY_EXPANSION = {
    "technology": ["Software Development", "Information Technology & Services", "Computer Software", "Internet"],
    "software": ["Software Development", "Computer Software"],
    "saas": ["Software Development", "Computer Software", "Internet"],
    "financial services": ["Financial Services", "Banking", "Insurance"],
    "fintech": ["Financial Services", "Banking"],
    "healthcare": ["Healthcare", "Hospital & Health Care"],
    "life sciences": ["Biotechnology", "Pharmaceuticals", "Medical Devices"],
    "public sector": ["Government Administration", "Public Sector"],
    "recruiting": ["Staffing & Recruiting", "Staffing and Recruiting", "Human Resources"],
    "executive search": ["Staffing & Recruiting", "Staffing and Recruiting", "Management Consulting"],
    "staffing": ["Staffing & Recruiting", "Staffing and Recruiting"],
    "consulting": ["Management Consulting"],
    "hr": ["Human Resources", "Human Resources Services"],
    "marketing": ["Marketing & Advertising"],
    "real estate": ["Real Estate", "Commercial Real Estate"],
    "manufacturing": ["Manufacturing", "Industrial Automation"],
    "retail": ["Retail", "Consumer Goods"],
    "education": ["Education", "E-Learning", "Higher Education"],
    "legal": ["Legal Services", "Law Practice"],
    "logistics": ["Logistics & Supply Chain", "Transportation/Trucking/Railroad"],
    "media": ["Media & Entertainment", "Online Media"],
}

# ── AI Ark enums (validation helpers) ─────────────────────────────────────────
SENIORITIES = ["founder", "owner", "partner", "c_suite", "vp", "director",
               "head", "manager", "senior", "mid-level", "entry", "intern"]
DEPARTMENTS = ["SALES", "MARKETING", "ENGINEERING", "FINANCE", "HR", "OPERATIONS",
               "SUPPORT", "IT", "LEGAL", "PRODUCT", "DESIGN", "EXECUTIVE", "CONSULTING",
               "EDUCATION", "MEDICAL", "ARTS", "ADMINISTRATIVE", "ACCOUNTING",
               "BUSINESS_DEVELOPMENT", "CUSTOMER_SUCCESS", "DATA", "RESEARCH"]


def expand_regions(regions):
    """['GCC','UK'] → ['United Arab Emirates',...,'United Kingdom'] (deduped, order-preserving)."""
    out = []
    for r in regions or []:
        for c in REGION_EXPANSION.get(str(r).strip().lower(), [r]):
            if c not in out:
                out.append(c)
    return out


def expand_industries(verticals):
    """['executive search'] → AI Ark industry strings (deduped, order-preserving)."""
    out = []
    for v in verticals or []:
        for i in INDUSTRY_EXPANSION.get(str(v).strip().lower(), [v]):
            if i not in out:
                out.append(i)
    return out
