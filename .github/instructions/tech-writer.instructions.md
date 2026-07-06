---
description: "Local instruction sheet for the Tech Writer agent. Loaded explicitly by the Tech Writer agent — do not load in any other agent."
---

# Tech Writer — local instructions

## Inputs

Every task run receives:

- **Jira issue ID**
- **Task** — one of the numbered tasks defined by the skills in `.github/skills/`

Perform the specified task on the relevant Jira issue.

## Task index

| #  | Task                       | Skill                          |
|----|----------------------------|--------------------------------|
| 1  | Categorization (AKA Begin) | `01-categorize`                |
| 2  | Context                    | `02-context`                   |
| 3  | Preliminary scope          | `03-preliminary-scope`         |
| 4  | Structural review          | `04-structural-review`         |
| 5  | Structuring                | `05-structuring`               |
| 6  | Cleaning                   | `06-cleaning`                  |
| 7  | Working files              | `07-working-files`             |
| 8  | Populate children          | `08-populate-children`         |
| 9  | Scope microcopy            | `09-scope-microcopy`           |
| 10 | Scope help center          | `10-scope-help-center`         |
| 11 | Approve scope              | `11-approve-scope`             |
| 12 | Scope Pendo                | `12-scope-pendo`               |
| 13 | Draft microcopy            | `13-draft-microcopy`           |
| 14 | Create help center PR      | `14-create-help-center-pr`     |
| 15 | Publish to knowledge base  | `15-publish-to-knowledge-base` |

## Sequencing and manual-trigger checkpoints

Most tasks flow directly into the next, but **stop and wait for a manual trigger** at these
checkpoints:

- **After Task 2 (Context):** a TW reviews Categorization and Context.
- **After Task 4 (Structural review):** a TW reviews Preliminary scope and Structural review.

Direct progressions when not at a checkpoint:

- Task 1 → Task 2 (only if the issue can be categorized)
- Task 3 → Task 4
- Task 5 → Task 6 → Task 7

All other tasks (8–15) are triggered individually unless the prompt says otherwise.

After completing any task, update the **TW Agent status** section in the issue description
and end with the response format defined in these instructions.

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

## Response format

End every task response with:

- **Steps completed (by last prompt):** [brief summary of what was completed]
- **Next step in sequence:** [the next numbered task or "Stop and wait for manual trigger"]
