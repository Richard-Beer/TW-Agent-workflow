# Cin7 Technical Writer agent — repository instructions

This repository powers a **Technical Writer** agent that performs a fixed sequence of
tasks on Cin7 Jira issues. The agent (`.github/agents/Tech Writer.agent.md`) is a thin
orchestrator; each task lives in its own skill under `.github/skills/`. These
instructions hold the conventions that apply across every task.

## Inputs

Every task run receives:

- **Jira issue ID**
- **Task** — one of the numbered tasks defined by the skills in `.github/skills/`

Perform the specified task on the relevant Jira issue.

## Script and path conventions

- Google Drive helper: `Scripts/google_drive/drive.py`. Run it from that folder, e.g.
  `cd "c:\Users\RichardBeer\Repos\TW Tech Writer agent\Scripts\google_drive"; python -B drive.py ...`
- Always run Python with `python -B` (suppresses `__pycache__` creation).
- To add rows to a Google Sheet, use `append_rows()` from `drive.py` — never the Sheets
  API `append` call directly (it inherits formatting from the nearest populated row).
- TW team Google Drive parent folder ID: `1YhXSSv6EPb_-td-bajDE2ev3P-RLZNNL`
- Markdown knowledge base repo: `c:\Users\RichardBeer\Repos\TW-Knowledge-bases-markdown`
  (Core articles in `Core/*.md`, Omni articles in `Omni/*.md`)
- MadCap Flare KB repos: `c:\Users\RichardBeer\Repos\Cin7 Core knowledge base` and
  `c:\Users\RichardBeer\Repos\Cin7 Omni knowledge base`

## Product model context

Model files describe the products' structure and vocabulary:

- `Models/Core model.md` — Cin7 Core navigation architecture (level-1 and level-2 locations)
- `Models/Omni model.md` — Cin7 Omni navigation architecture (level-1 and level-2 locations)
- `Models/Pendo model.md` — Pendo guide strategies, guide types, and content element vocabulary
- `Models/Core help center model.md` — Cin7 Core help center topic hierarchy

**Shared model context activation** — when a task needs product model context:

1. Determine product context from the issue: `Core`, `Omni`, or `Unknown`.
2. If `Core`, read `Models/Core model.md` **and** `Models/Core help center model.md`.
3. If `Omni`, read `Models/Omni model.md`.
4. If `Unknown`, do not guess. Use `Unknown` for product-specific details.

Tasks may additionally require `Models/Pendo model.md` when noted.

## Jira writing guidelines

- Use **bold** for headings inside Jira issue descriptions (not markdown `##` headings).
- Do not use section breaks in Jira issue descriptions.
- In markdown tables sent to Jira, wrap header cell text in `**bold**` explicitly — the
  markdown header syntax (`|---|`) does not render as bold in Jira's ADF.

## Workflow tracking in the Jira description

Keep a **TW Agent status** section at the top of the Jira issue description so anyone can
see status at a glance. Color coding is unreliable in Jira markdown, so use text labels
plus strikethrough:

- Completed steps: prefix with `[DONE]` and strike through the full line with `~~...~~`
- Remaining steps: prefix with `[TO DO]` and do not strike through

Required format:

```
**TW Agent status**

- [TO DO] 1 - Categorization (AKA Begin)
- [TO DO] 2 - Context
- [TO DO] 3 - Preliminary scope
- [TO DO] 4 - Structural review
- [TO DO] 5 - Structuring
- [TO DO] 6 - Cleaning
- [TO DO] 7 - Working files
- [TO DO] 8 - Populate children
- [TO DO] 9 - Scope microcopy
- [TO DO] 10 - Scope help center
- [TO DO] 11 - Approve scope
- [TO DO] 12 - Scope Pendo
- [TO DO] 13 - Draft microcopy
- [TO DO] 14 - Create help center PR
- [TO DO] 15 - Publish to knowledge base
```

After completing any task (or group of tasks in one run), immediately update this section:

- Convert each completed step line to `[DONE]` and strike it through
- Leave all remaining steps as `[TO DO]`
- Keep step numbering unchanged
- Keep this section at the top of the description after each update

## Due date handling

Set the Jira issue **Due date** only when it can be identified confidently from a linked
issue's planned release date.

- Source of truth: the linked issue's release date (or an explicit release date on it)
- Be conservative: if multiple plausible dates exist, choose the earliest credible one
- If the release date cannot be identified confidently, leave the Due date blank
- Do not infer from vague language (for example, "soon", "next sprint", or quarter-only)

## Response format

End every task response with:

- **Steps completed (by last prompt):** [brief summary of what was completed]
- **Next step in sequence:** [the next numbered task or "Stop and wait for manual trigger"]
