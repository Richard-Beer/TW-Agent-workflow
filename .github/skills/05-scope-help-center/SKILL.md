---
name: 05-scope-help-center
description: 'Task 5 of the Tech Writer workflow. Use to do a targeted + broad review of Core/Omni markdown knowledge base articles for a Cin7 Jira issue, recording a Help center scope table in the issue description.'
argument-hint: 'Jira issue ID'
---

# Task 5 — Scope help center

Using the pre-written detailed summary, identify what help center changes are required
for this issue.

## Starting point

Read the `### UX change (detailed)` or `### Problem (detailed)` section from the issue
description (the heading depends on the issue category). If this task is running on a
child issue, read it from the parent issue description instead.

This section, written in Task 1, is the authoritative list of UI changes for this issue.
Do not re-examine sources to determine what changed.

If the issue description does not contain either section, note this in the Help center
scope table rationale and proceed using the available issue context.

## Microcopy context

Before scoping articles, check whether microcopy information is available for this issue:

1. If this task is running on a subtask, check sibling subtasks for a **Microcopy**
   subtask. If one exists, read its **Working file** link (a Google Sheet) and review the
   populated rows for additional context on text changes.
2. If this task is running on the story itself, check the **Working files** section for a
   Microcopy sheet link and review it if present.
3. If no microcopy sheet or summary is found, proceed without it — this is not an error.

Use any microcopy context found to inform your assessment of which articles reference
changing text, labels, or terminology.

## Stage 1 — Targeted article review

Determine whether the relevant knowledge base is Core or Omni (or both) based on the
product context.

The knowledge base articles are markdown files in the `TW-Knowledge-bases-markdown` repo:

- **Omni:** `Omni/*.md`
- **Core:** `Core/*.md`

Open the appropriate TOC file to identify the relevant subtopics:

- **Omni:** `Omni/_Metadata/TOC.md`
- **Core:** `Core/_Metadata/TOC.md`

The TOC is a markdown hierarchy where `##` headings represent topics, `###` headings
represent subtopics, and bullet items under subtopics represent article titles. Updates
typically affect subtopics within a topic, not entire topics.

For integration-related issues, note that integration help follows a hub-and-spoke
pattern: one main overview article branching to support articles, with optional
second-level overviews for larger integrations.

Read the articles within the relevant subtopics. For each article, determine whether it
needs to be:

- **Deleted** — the article is made obsolete by the update
- **Updated** — the article references UX elements, microcopy, or processes that are
  changing
- **Created** — the update introduces new functionality that requires a new article

Provide a rationale for each proposed change.

## Stage 2 — Broad KB sweep

Search across all articles in the relevant knowledge base markdown folder (`Core/` or
`Omni/`) for:

- References to microcopy that is changing
- References to UI elements that are being added, changed, or removed
- References to processes or workflows that are changing
- Opportunities to link to or contextually surface the feature (in a use-case sense, not
  promotional)

Report any additional articles found that were not already identified in Stage 2.

## Output

Add a new section to the issue description:

```
### Help center scope

| Article | Action | Rationale |
|---|---|---|
| **Primary updates** | | |
| [Article title] | [Delete/Update/Create] | [Why] |
| ... | | |
| **Secondary updates** | | |
| [Article title] | [Delete/Update/Create] | [Why] |
| ... | | |
```

Primary updates are articles within the most relevant subtopics (Stage 1). Secondary
updates are articles found in the broad KB sweep (Stage 2).
