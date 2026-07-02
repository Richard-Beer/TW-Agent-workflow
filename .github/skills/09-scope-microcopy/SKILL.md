---
name: 09-scope-microcopy
description: 'Task 9 of the Tech Writer workflow. Use to analyze UI changes for a Cin7 Jira issue and populate microcopy requirements (Location, Element, Current, Notes) into the Microcopy working Google Sheet, plus a summary in the issue description.'
argument-hint: 'Jira issue ID'
---

# Task 9 — Scope microcopy

Gather and analyze available resources to define the microcopy requirements for the issue.

## Discovery

Collect relevant materials from the following sources only:

- The issue, its parent, its children, and any issues linked to any of those
- External files (e.g. Figma designs, Confluence pages, Google Drive docs) that are
  explicitly referenced in or attached to one of the above issues

Do not browse third-party apps independently to find additional resources.

## Analysis

Using the gathered resources, identify microcopy requirements by examining the UI changes
involved:

- Identify existing app pages that have microcopy requirements (new, updated, or deleted
  microcopy)
- Identify new app pages (all microcopy will be new, or migrated from an existing page)
- Identify existing app pages that will be deleted (microcopy will be deleted or migrated
  to another page)

For each affected page — except those being deleted — determine:

- What new microcopy is needed
- What existing microcopy needs updating
- What existing microcopy needs deleting

## Output

Add the microcopy requirements to the Microcopy working file (Google Sheet) linked in the
issue's **Working files** section. Populate one row per microcopy item using the sheet's
seven columns:

| Column | Content | Who populates |
|---|---|---|
| Location | The app page or area where the microcopy appears | Agent |
| Element | The specific UI element (e.g. button label, tooltip, field placeholder) | Agent |
| Current | The existing text if you are confident of it; `UNKNOWN` if you are unsure; `NEW` if the element is new and has no existing microcopy | Agent |
| New | Leave blank for now (populated in Task 13) | Agent (leave blank) |
| Notes | Any additional context, such as whether the item is new, updated, or deleted | Agent |
| Questions/Comments | Feedback or open questions for Product/Design (optional; typically completed after Task 13) | Manual |
| QA | QA sign-off or review status (optional; typically completed post-draft) | Manual |

Populate Location, Element, Current, and Notes columns only; leave New,
Questions/Comments, and QA blank.

Group rows by page, adding a blank row between each page's items for readability. Include a
row for each microcopy item on pages being deleted, leaving **Current** as "DELETE",
**New** blank, and noting why in the **Notes** column.

For dialogs/modals, use a single row per dialog/modal and represent the text in plain text
segments separated by `|` in this order: Heading | Body | CTA 1 | CTA 2 (add more CTA
segments if needed).

Also add a brief summary of the microcopy requirements to the issue description, organized
by page.
