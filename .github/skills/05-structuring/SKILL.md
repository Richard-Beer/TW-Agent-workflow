---
name: 05-structuring
description: 'Task 5 of the Tech Writer workflow. Use to apply the Structuring advice for a Cin7 Jira issue — promoting the issue, creating child issues, or adding subtasks — then proceed to Cleaning.'
argument-hint: 'Jira issue ID'
---

# Task 5 — Structuring

Apply the restructuring advice from the **Structuring advice** section — for example,
promoting the issue to an epic, creating child issues, or adding subtasks as recommended.

## Child issue names

When creating child issues, use exactly these names — no parent issue key prefix, no other
identifier:

| Deliverable | Child issue name |
|---|---|
| Microcopy | `Microcopy` |
| Help center | `Help center` |
| Pendo guides | `Pendo` |
| EAP | `EAP` |

## Parent epic assignment

After structuring, set the parent epic for the issue (or new epics/stories created) based
on the issue's category (determined in Task 1):

**If the issue was promoted to an epic:**
- Assign the new epic's parent to:
  - `OTW-1616` — if category is **Release**
  - `OTW-1617` — if category is **Foundations** or **Enablement**
- Assign each new child story's parent to the new epic.

**If the issue stays as a story:**
- Assign the story's parent epic to:
  - `OTW-1862` — if category is **Release**
  - `OTW-1619` — if category is **Foundations**
  - `OTW-1633` — if category is **Enablement**

The category is visible on the issue (set during Task 1 as the issue type: Feature Request
= Release, Doc Request = Foundations, Task = Enablement).

## Next step

Once you complete the Structuring step, immediately proceed to **Task 6 — Cleaning**.
