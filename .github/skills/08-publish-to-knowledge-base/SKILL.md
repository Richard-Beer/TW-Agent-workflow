---
name: 08-publish-to-knowledge-base
description: 'Task 8 of the Tech Writer workflow. Use to convert updated markdown articles back to MadCap Flare HTM files in the local Core/Omni KB repos via the conversion script. Writes to the filesystem only — no commit or push.'
argument-hint: 'Jira issue ID'
---

# Task 8 — Publish to knowledge base

Convert the updated markdown articles back to MadCap Flare HTM files and write them to the
local knowledge base repository.

> **Prerequisite:** this task depends on `Scripts/convert-markdown-to-html.py`. That script
> is not currently present in this repo — add it before running this task.

## When to run this task

Run this task after the Help center markdown work is complete and reviewed — typically
after Task 7 (Create help center PR) has been raised. This task writes directly to the
local KB repo filesystem; it does not push or commit anything.

## Steps

1. Read the issue to identify:
   - The issue key (e.g. `OTW-1234`)
   - The product context — **Core** or **Omni** (or both)

2. Check out the issue branch in the markdown repo:

   ```
   cd c:\Users\RichardBeer\Repos\TW-Knowledge-bases-markdown
   git checkout <issue_key>
   git pull
   ```

3. Identify the changed `.md` files:

   ```
   git diff --name-only master...<issue_key>
   ```

4. Run the conversion script for each changed file, specifying files explicitly:

   ```
   python -B Scripts/convert-markdown-to-html.py Core "Core/Article name.md" "Core/Another article.md"
   ```

   Or to convert all files for a product at once:

   ```
   python -B Scripts/convert-markdown-to-html.py Core
   ```

   Use `Omni` instead of `Core` for Omni knowledge base articles.

## What the script does

- Writes `.htm` files to
  `c:\Users\RichardBeer\Repos\Cin7-Core-knowledge-base\Content\Resources\Topics\` (or Omni
  equivalent)
- Converts markdown syntax back to MadCap Flare XML elements (`<MadCap:variable>`,
  `<MadCap:snippetBlock>`, `<div class="note/warning/overview">`, etc.)
- If the inlined content inside a `:::snippet` block has changed, updates the corresponding
  `.flsnp` file in the KB repo's Snippets folder
- Preserves the existing `<head>` block of each article on update; generates a minimal head
  for new articles
- Does **not** push or commit to any repository

## After running

Confirm the expected `.htm` files were written by checking the output. If any snippet files
were updated, note them for the commit to the KB repo.

## Limitations

- `MadCap:conditions` attributes are not reconstructed (they were not preserved by the
  markdown conversion)
- Named anchors (`<a name="...">`) are only restored in articles that were originally
  converted to markdown *after* the named-anchor fix was applied to
  `convert-html-to-markdown.py`; articles converted before that fix will not have their
  anchors in the HTM output
