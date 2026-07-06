# Cin7 TW agents — shared repository instructions

These instructions hold the shared conventions that apply across all agents in this
repository — script and path rules, Jira reading and writing standards, product model
activation, and due-date handling. Agent-specific workflows, inputs, and response
formats live in each agent's local instruction sheet under `.github/instructions/`.

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

- `Models/Article model.md` — article types, content types, and standard sections by product
- `Models/Core model.md` — Cin7 Core navigation architecture (level-1 and level-2 locations)
- `Models/Omni model.md` — Cin7 Omni navigation architecture (level-1 and level-2 locations)
- `Models/Pendo model.md` — Pendo guide strategies, guide types, and content element vocabulary
- `Models/Core help center model.md` — Cin7 Core help center topic hierarchy

**Model loading — at the start of every task:**

1. Always read `Models/Pendo model.md` and `Models/Article model.md`.
2. Determine product context from the issue or source material: `Core`, `Omni`, or `Unknown`.
3. If `Core`, read `Models/Core model.md` and `Models/Core help center model.md`.
4. If `Omni`, read `Models/Omni model.md`.
5. If `Unknown`, do not load either product model and do not guess product-specific details.

## Working with Jira

Read and write Jira through the Atlassian tools by capability, not by a fixed tool name:

- **Reading issue content** — fetch the issue by its key to get the authoritative, full
  description before acting on it. Do not rely on search results as the source of an
  issue's description: search returns summarized or truncated snippets and is only for
  discovery (finding related issues, children, or linked issues).
- **Before any description edit** — re-read the issue immediately beforehand and base your
  edit on that latest version. Humans review and edit descriptions at the manual-trigger
  checkpoints, so acting on a stale copy risks overwriting their changes.
- **On a write failure** — if setting the issue type, transitioning, editing the
  description, or creating a child issue fails (for example, a permission error or an
  invalid transition), do not retry blindly or guess an alternative. Add a
  `[TW Agent] <operation> failed` note to the issue description, report it in the response,
  and stop.

## Jira writing guidelines

- Use `###` (H3) for top-level section headings in Jira issue descriptions; use `####` (H4)
  for sub-headings within a section. Do not use H1 or H2. Bold is for inline emphasis only.
- Do not use section breaks in Jira issue descriptions.
- In markdown tables sent to Jira, wrap header cell text in `**bold**` explicitly — the
  markdown header syntax (`|---|`) does not render as bold in Jira's ADF.

## Due date handling

Set the Jira issue **Due date** only when it can be identified confidently from a linked
issue's planned release date.

- Source of truth: the linked issue's release date (or an explicit release date on it)
- Be conservative: if multiple plausible dates exist, choose the earliest credible one
- If the release date cannot be identified confidently, leave the Due date blank
- Do not infer from vague language (for example, "soon", "next sprint", or quarter-only)

