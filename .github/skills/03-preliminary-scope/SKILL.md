---
name: 03-preliminary-scope
description: 'Task 3 of the Tech Writer workflow. Use to produce a detailed UX change summary for a Cin7 Jira issue, then identify at a high level which deliverables (Help center, Microcopy, Pendo guides, EAP) are in or out of scope, recording both in the issue description.'
argument-hint: 'Jira issue ID'
---

# Task 3 — Preliminary scope

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

Add the UX change summary to the issue description in the following format:

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
```

## Stage 2 — Deliverable identification

Based on the UX change summary above, identify roughly what deliverables Technical Writing
needs to produce.

Deliverables may include:

- **Help center** — creating, updating, deleting, or otherwise changing help center
  articles, subtopics, or topics
- **Microcopy** — creating, updating, deleting, or otherwise changing UI text
- **Pendo guides** — creating, updating, deleting, or otherwise changing Pendo guides
- **EAP** — creating, updating, deleting, or otherwise changing Early Access Program
  documentation

You are not to plan out the deliverables in detail, but rather identify positively or
negatively whether each of these deliverables is likely to be in scope. The one exception
is that if the Request (original) explicitly calls for a specific deliverable, you should
mark that deliverable as in scope.

Add this information to the issue description in a new section called **Request
(refined)** with a section for in-scope and out-of-scope deliverables. Note explicitly
where the Requirements contradict or go beyond the Request (original) (if any).

Once you complete the Preliminary scope, proceed to **Task 4 — Structural review**.