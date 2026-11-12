---
name: miro
description: Read, create and update Miro boards through the Miro MCP server - flowcharts, process maps, workshop boards, campaign architecture diagrams, org and account maps. Use when someone asks to make or edit a Miro board, draw a flow or diagram in Miro, read what is on a board, or turn a doc into a visual.
---

# Miro (MCP)

Claude Code talks to Miro through Miro's hosted MCP server (`https://mcp.miro.com/`). The repo's
`.mcp.json` carries a `miro` entry, so it arrives with `gtm-work` like any other update. If it is
missing on your machine, add it once:

```bash
claude mcp add --transport http -s user miro https://mcp.miro.com/
```

## First use (once per person)

1. Launch with `gtm-work`. If Claude asks whether to approve the `miro` MCP server, say yes.
2. Type `/mcp`, pick **miro**, and sign in to Miro in the browser tab that opens. Use your own
   Miro account; boards are created as you.
3. Check it: ask Claude "who am I in Miro?" (`mcp__miro__user_who_am_i`).

If the tools are missing, `/mcp` shows why (usually "needs authentication").

## How Claude must use it

**Always load the Canvas Composer guide first.** Before creating or editing anything call
`mcp__miro__canvas_get_canvas_composer_skill` and follow its design and SVG steps. The
`canvas_*` tools speak a specific SVG dialect and guessing it produces broken boards.

| Job | Tool |
|---|---|
| New board | `board_create` |
| Find a board | `board_search_boards` |
| Read what's on a board | `canvas_read_as_svg`, `canvas_search` |
| Add content | `canvas_create_from_svg` |
| Change existing content | `canvas_update_from_svg` |
| Comments | `comment_list_comments`, `comment_create`, `comment_reply` |
| Tables | `table_create`, `table_sync_rows` |

### Flowcharts (the thing we make most)

Use the diagram widget, which renders Mermaid inside a fixed 1600x900 box:

```svg
<g id="f1" transform="translate(0,200)" data-frame="Setup">
  <rect data-type="frame" x="0" y="0" width="1728" height="1028" fill="#ffffff" />
  <foreignObject id="d1" x="64" y="64" width="1600" height="900" data-type="diagram" data-title="Setup">
flowchart TD
    a(["Start"]) --&gt; b["Step"] --&gt; c{{"Decision?"}}
  </foreignObject>
</g>
```

- Escape inside the SVG: `-->` becomes `--&gt;`, `&` becomes `&amp;`. No raw `<`, `>` or `&`.
- Quote every Mermaid label: `n1["Text"]`, `n2{{"Question?"}}`, `n3(["Start"])`.
- One idea per frame. Put frames on a grid (we use a 2048 column pitch and 160 to 320 gaps).
- Colour meaning (reuse it so boards read the same): yellow `#FFE86D` = a person does this,
  grey `#DDDDD8` = automatic, blue `#9CE6FF` = decision, green `#B3E65F` = start/finish,
  orange `#FFB575` = blocked or a known gap.
- No em dashes in board text.
- **Changing a diagram that's already on a board:** don't send `canvas_update_from_svg` on the
  diagram itself. Measured 2026-09-22: that pulls it out of its frame to a random spot, and x/y
  can't be updated to move it back. `canvas_create_from_svg` with `?moveToWidget=<frame>` also
  landed outside the frame (auto-placement). What works: `canvas_update_from_svg` with the
  frame's `<g ... data-miro-id="<frame id>">` wrapping a NEW `foreignObject` (no miro-id). That
  creates the diagram inside the frame. Then delete the old one, after the user confirms.

## Rules

- **Miro boards are outward-facing.** Anyone a board is shared with (a prospect, a partner) can
  see it. Confirm before editing a board you did not create in this session, and never delete
  someone else's content.
- Read before you write: `canvas_read_as_svg` on the area first so new frames do not land on
  top of existing ones.
- Never put API keys, internal pricing, customer data or anything confidential on a board that is
  shared outside the company.
- Save the board URL in the play's `plays/<play-slug>/PLAY.md` or in
  `company/context.md` for company-wide boards, so it can be found again.
