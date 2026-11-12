---
name: list-dedup
description: Deduplicate contact and company lists by AI Ark id, LinkedIn URL, domain and company name, and check a new list against every CSV already in plays/. Use before enrichment or any per-row paid step to save credits.
---

# List Deduplication

Remove duplicate records from contact and company lists before enrichment (to save credits) and after combining sources (to remove cross-source dupes).

---

## Do We Already Have Them? (run before any paid pull)

Every list you have paid for lives as a CSV under `plays/*/leads/`. Check a new set of domains (or
AI Ark ids) against all of them before you search or enrich:

```python
import csv, glob

def held(col_candidates, pattern="plays/*/leads/**/*.csv"):
    out = set()
    for path in glob.glob(pattern, recursive=True):
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                for col in col_candidates:
                    v = (row.get(col) or "").strip().lower()
                    if v:
                        out.add(v)
    return out

held_domains = held(["website", "company_website", "domain", "Company Domain"])
new = [d for d in my_domains if normalize_domain(d) not in held_domains]
```

For AI Ark pulls the script does this for you: `aiark.py ... --known <old csvs> --new-only`.

---

## When to Dedup

| Timing | Why | Key |
|--------|-----|-----|
| **Before enrichment** | Save credits -- do not pay to enrich the same person twice | LinkedIn URL |
| **After combining sources** | Remove cross-source dupes when merging CSVs from AI Ark, Ocean, Exa, Clay, etc. | AI Ark id, then LinkedIn URL |
| **After scoring** | Keep highest-scored entry when same company appears multiple times | Company name |

---

## Primary Dedup Key: AI Ark id, then LinkedIn URL

Within AI Ark output, `ai_ark_people_id` / `ai_ark_account_id` are exact keys; use them first.
Across sources, LinkedIn URL is the single best dedup key for contacts. Always normalize before comparing.

### Normalization

```python
import re

def normalize_linkedin_url(url):
    """Normalize LinkedIn URL for dedup comparison."""
    if not url:
        return ""
    url = url.strip()
    url = re.sub(r'^https?://', '', url)    # Strip protocol
    url = re.sub(r'^www\.', '', url)         # Strip www
    url = url.rstrip('/')                     # Strip trailing slash
    url = url.split('?')[0]                   # Strip query params
    return url.lower()                        # Lowercase
```

**Why normalize?** The same profile can appear as:
- `https://www.linkedin.com/in/janesmith`
- `https://linkedin.com/in/janesmith/`
- `http://www.linkedin.com/in/janesmith?locale=en_US`
- `linkedin.com/in/JaneSmith`

All four should resolve to: `linkedin.com/in/janesmith`

### Dedup by Person LinkedIn URL

```python
seen = set()
unique = []
dupes = 0

for contact in all_contacts:
    person_li = normalize_linkedin_url(contact.get('Person LinkedIn URL', ''))
    if person_li and person_li in seen:
        dupes += 1
        continue
    if person_li:
        seen.add(person_li)
    unique.append(contact)

print(f"Removed {dupes} duplicates, {len(unique)} unique contacts")
```

**Important:** Contacts with empty LinkedIn URLs are kept (not deduped). They may be valid contacts missing profile data.

---

## Secondary Dedup Key: Company Name

Use for company-level dedup when the same company appears multiple times (common when several exports are merged).
Prefer the **domain** when you have it: strip protocol, `www.` and path, lowercase. Names collide (two "Acme Inc"s), domains rarely do.

```python
def normalize_domain(d):
    d = (d or "").strip().lower()
    d = re.sub(r'^https?://', '', d)
    d = re.sub(r'^www\.', '', d)
    return d.split('/')[0]
```

### Dedup by Company Name (Keep Highest Score)

```python
best = {}
for company in scored_companies:
    name = company['Company Name'].strip().lower()
    if name not in best or company['Score'] > best[name]['Score']:
        best[name] = company

unique_companies = list(best.values())
```

### Company LinkedIn URL Dedup

For company lists where you have LinkedIn company URLs:

```python
def normalize_company_url(url):
    """Same normalization as person URLs."""
    if not url:
        return ""
    url = url.strip()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.rstrip('/')
    url = url.split('?')[0]
    return url.lower()

seen = set()
unique = []
for company in companies:
    co_li = normalize_company_url(company.get('Company LinkedIn URL', ''))
    if co_li and 'linkedin.com/company' in co_li:
        if co_li in seen:
            continue
        seen.add(co_li)
    unique.append(company)
```

---

## Multi-Source Combine Pattern

When merging contacts from multiple CSVs (AI Ark pulls, a Clay export, a CRM export):

### Step 1: Load and Normalize Columns

Different sources use different column names. Map them to a standard schema.

```python
COLUMN_MAP = {
    # Source column → Standard column
    # aiark.py people CSV
    'full_name': 'Full Name',
    'title': 'Title',
    'linkedin': 'Person LinkedIn URL',
    'company_name': 'Company Name',
    'company_website': 'Company Domain',
    'company_linkedin': 'Company LinkedIn URL',
    # other exports often use
    'Name': 'Full Name',
    'Personal LinkedIn Url': 'Person LinkedIn URL',
    'Domain': 'Company Domain',
}

def normalize_row(row, source_name, column_map=None):
    """Map source-specific columns to standard schema."""
    normalized = {}
    for src_col, std_col in (column_map or COLUMN_MAP).items():
        normalized[std_col] = row.get(src_col, '') or row.get(std_col, '')
    normalized['Source'] = source_name
    return normalized
```

### Step 2: Load All Sources

```python
sources = [
    ("plays/<play-slug>/leads/contacts/aiark-pull-1.csv", "AI Ark pull 1"),
    ("plays/<play-slug>/leads/contacts/aiark-pull-2.csv", "AI Ark pull 2"),
    ("plays/<play-slug>/leads/contacts/clay-export.csv", "Clay Export"),
]

all_contacts = []
for filepath, source_name in sources:
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            normalized = normalize_row(row, source_name)
            all_contacts.append(normalized)

print(f"Combined raw: {len(all_contacts)}")
```

### Step 3: Dedup

```python
seen = set()
unique = []
for contact in all_contacts:
    li_url = normalize_linkedin_url(contact.get('Person LinkedIn URL', ''))
    if li_url and li_url in seen:
        continue
    if li_url:
        seen.add(li_url)
    unique.append(contact)

print(f"After dedup: {len(unique)}")
```

### Step 4: Sort and Export

```python
unique.sort(key=lambda c: (
    c.get('Tier', 'Tier 9'),      # Tier 1 first
    c.get('Persona Code', ''),     # Group by persona
    c.get('Company Name', '').lower()
))

headers = ['Full Name', 'Title', 'Company Name', 'Company Domain',
           'Company LinkedIn URL', 'Person LinkedIn URL', 'Tier', 'Source']

with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    for c in unique:
        writer.writerow({h: c.get(h, '') for h in headers})
```

---

## Per-Company Contact Caps

Limit the number of contacts per company to avoid saturation. Typical cap: 5-10 contacts per company.

### Implementation

```python
from collections import defaultdict

TITLE_PRIORITY = {
    'c-suite': 1, 'vp': 2, 'director': 3,
    'head': 4, 'manager': 5, 'senior': 6, 'other': 7
}

def title_score(title):
    """Return priority score (lower = more senior)."""
    t = (title or '').lower()
    if any(x in t for x in ['chief', 'ceo', 'cfo', 'cmo', 'cro', 'coo']):
        return 1
    if any(x in t for x in ['vp', 'vice president', 'svp', 'evp']):
        return 2
    if 'director' in t:
        return 3
    if 'head of' in t or 'head,' in t:
        return 4
    if 'manager' in t:
        return 5
    return 6

MAX_PER_COMPANY = 10

# Group by company
by_company = defaultdict(list)
for contact in unique_contacts:
    key = normalize_linkedin_url(contact.get('Company LinkedIn URL', ''))
    if not key:
        key = contact.get('Company Name', '').strip().lower()
    by_company[key].append(contact)

# Cap per company, keeping most senior
capped = []
for company_key, contacts in by_company.items():
    contacts.sort(key=lambda c: title_score(c.get('Title', '')))
    capped.extend(contacts[:MAX_PER_COMPANY])
```

---

## Cross-Reference Against TAM

After deduplication, cross-reference contacts against the TAM company list to:
1. Assign tier labels
2. Remove contacts at companies not in the TAM

```python
def load_tam(tam_filepath):
    """Load TAM: normalized company LinkedIn URL -> tier."""
    tam = {}
    with open(tam_filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = normalize_linkedin_url(row.get('Company LinkedIn URL', ''))
            if url and 'linkedin.com/company' in url:
                tam[url] = row.get('Tier', '')
    return tam

tam = load_tam('plays/<play-slug>/leads/companies/tam_scored.csv')

matched = []
for contact in unique_contacts:
    co_url = normalize_linkedin_url(contact.get('Company LinkedIn URL', ''))
    if co_url in tam:
        contact['Tier'] = tam[co_url]
        matched.append(contact)
```

---

## Checklist

- [ ] Normalize all LinkedIn URLs before any comparison
- [ ] Dedup contacts by Person LinkedIn URL (primary key)
- [ ] Dedup companies by Company LinkedIn URL or company name
- [ ] When combining sources, map columns to standard schema first
- [ ] Keep contacts with empty LinkedIn URLs (do not auto-discard)
- [ ] Apply per-company contact caps (5-10 per company)
- [ ] Cross-reference contacts against TAM for tier assignment
- [ ] Sort output: Tier 1 first, then by persona, then by company name
- [ ] Print dedup stats (total raw, dupes removed, final unique count)

---

## References

- Keep each play's combine/dedup script next to its output in `plays/<play-slug>/leads/contacts/`.
- `skills/ai-ark/aiark.py --known ... --new-only` for AI Ark-id de-dup at pull time.
- `skills/tam-scoring` for the scored TAM this cross-references.
