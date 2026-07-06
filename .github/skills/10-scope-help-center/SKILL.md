---
name: 10-scope-help-center
description: 'Task 10 of the Tech Writer workflow. Use to produce a detailed UX change summary and a targeted + broad review of Core/Omni markdown knowledge base articles for a Cin7 Jira issue, recording UX change summary and Scope tables in the issue description.'
argument-hint: 'Jira issue ID'
---

# Task 10 — Scope help center

Gather and analyze available resources to define what help center changes are required for
this issue.

## Stage 1 — UX change summary (detailed)

Collect relevant materials from the following sources only:

- The issue, its parent, its children, and any issues linked to any of those
- External files (e.g. Figma designs, Confluence pages, Google Drive docs) explicitly
  referenced in or attached to one of the above issues

Using the gathered resources, produce a detailed summary of all UX changes:

- **Visible changes:** design changes (new/changed/removed pages, buttons, toggles,
  fields, or other interactive UI elements) and microcopy changes (labels, messages,
  tooltips, placeholders)
- **Functional changes:** behind-the-scenes logic changes (e.g. different journals
  created, data mapping changes, workflow changes, new validations)

Note explicitly if a Figma file or microcopy document could not be found.

## Stage 2 — Targeted article review

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

## Stage 3 — Broad KB sweep

Search across all articles in the relevant knowledge base markdown folder (`Core/` or
`Omni/`) for:

- References to microcopy that is changing
- References to UI elements that are being added, changed, or removed
- References to processes or workflows that are changing
- Opportunities to link to or contextually surface the feature (in a use-case sense, not
  promotional)

Report any additional articles found that were not already identified in Stage 2.

## Output

Add two new sections to the issue description:

```
### UX change summary (detailed)

| Change | Type | Details |
|---|---|---|
| **Visible changes** | | |
| [Element or page] | [Added/Changed/Removed] | [Description] |
| ... | | |
| **Functional changes** | | |
| [Behaviour or logic] | [Added/Changed/Removed] | [Description] |
| ... | | |

**Sources:**
- [List of sources consulted, e.g. Figma file, microcopy document, linked issue]
- [Note any expected sources that were missing, e.g. "Figma file: not found"]

### Scope

| Article | Action | Rationale |
|---|---|---|
| **Primary updates** | | |
| [Article title] | [Delete/Update/Create] | [Why] |
| ... | | |
| **Secondary updates** | | |
| [Article title] | [Delete/Update/Create] | [Why] |
| ... | | |
```

Primary updates are articles within the most relevant subtopics (Stage 2). Secondary
updates are articles found in the broad KB sweep (Stage 3).
