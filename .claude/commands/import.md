Find Magna's scattered lists, decks and docs on this laptop and bring them into the repo.

Request: **$ARGUMENTS** (optional: extra names to search for, or a folder path)

## Steps

1. **Scan (read-only, nothing is copied):**
   ```
   python3 import_files.py scan [--also "other name,product"] [--path ~/Desktop/that-folder]
   ```
   It searches by the names in `company/import-terms.txt` with Spotlight and walks Desktop,
   Documents, Downloads and Google Drive / Dropbox / OneDrive folders.

2. **Show the candidates and recommend.** Where each is, how many files, how big, how recent, and
   which you'd bring in. Flag anything that looks unrelated or stale. Ask which numbers to import and
   where they go: `company` (positioning decks, use-case docs, one-pagers, ICP matrices) or a play
   (that play's lists and copy).

3. **Dry run, show the result:**
   ```
   python3 import_files.py apply --into company --pick 1,3-5 --dry-run
   ```
   Say how many files land where and name every file skipped for size (over 25MB stays on the laptop).

4. **On a yes, copy** (same command without `--dry-run`). Originals are never moved or deleted. Lead
   lists are logged in `leads/REGISTER.md`, every file in `IMPORT-LOG.md`.

5. **Fold the substance into context.** For decks and docs that land in `company/`, read them and
   propose additions to `company/context.md` (facts only, dated, sourced to the file). Apply what
   they approve.

6. `python3 files.py check`, then `/save`.

## Rules

- Never copy by hand anything the script skipped, especially a file flagged as holding a key.
- Confidential material (contracts, customer data under NDA, call recordings) stays out unless the
  person importing it confirms it may live in the repo.
- `.import/` holds laptop paths. It is gitignored; leave it that way.
