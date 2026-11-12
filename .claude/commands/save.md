Commit and push this session's work, and log it, so the next person picks up where you stopped.

## Steps

1. **See what changed:** `git status` and `git diff --stat`.

2. **Nothing stranded.** `python3 files.py check`. A list or deliverable outside `plays/` or
   `company/` is lost when the session ends. File it:
   ```
   python3 files.py add <play-slug|company> <file> --type contacts --source ai-ark --note "what it is"
   ```

3. **Commit** with a message in the form `[play-slug] what was done`:
   - `[saudi-banks-fraud] pull 240 CISOs from AI Ark and draft a 3-step sequence`
   - `[company] add the hospitality use-case deck and update the proof points`
   Leave out raw provider dumps, caches, `.env`, anything with a credential. Over a few MB: trim it.

4. **Push:** `git pull --rebase origin main && git push origin main`. Resolve conflicts with the
   person, never force-push.

5. **Log the session:**
   ```
   python3 gtm.py log-session --play <slug> --summary "<outcomes, not activity>" \
     --files "a.csv,b.md" --skills "ai-ark,instantly"
   ```
   "Built 412 hotel GMs across 6 SEA countries, drafted sequence v1" beats "worked on SEA".

6. **Offer to log what worked**, only with evidence behind it:
   ```
   python3 gtm.py log-intel --play <slug> --category copy_angle --label "<short name>" \
     --insight "<what happened and why it matters>" --recommendation "<what to do next>" \
     --sample-size N --reply-rate N.N --confidence medium
   ```
   Categories: copy_angle, subject_line, segment, persona, send_time, offer, cta, channel,
   list_source, deliverability, event, signal.

7. **Confirm** what was committed, pushed and logged. (Without a database, the logs are files in
   `log/` and travel with the commit, so commit after logging.)

## Rules

- Don't invent a summary. If unsure what was accomplished, ask.
- If nothing changed in the repo but real work happened elsewhere (a campaign loaded, replies
  worked), still log the session.
