---
description: "Local instruction sheet for the Tech Writer agent. Loaded explicitly by the Tech Writer agent — do not load in any other agent."
---

# Tech Writer — local instructions

## Inputs

Every task run receives:

- **Jira issue ID**
- **Task** — one of the numbered tasks defined by the skills in `.github/skills/`

Before doing anything else, confirm the supplied issue is a **story**. If it is any other
issue type (epic, subtask, task, bug, etc.), stop immediately and tell the user:

> This workflow only runs on story-type issues. Please supply a story ID.

Otherwise, perform the specified task on the relevant Jira issue.

## Task index

| #  | Task                      | Skill                          |
|----|---------------------------|--------------------------------|
| 1  | Intake                    | `01-intake`                    |
| 2  | Approve intake            | `02-approve-intake`            |
| 3  | Scope microcopy           | `03-scope-microcopy`           |
| 4  | Scope help center         | `04-scope-help-center`         |
| 5  | Approve help center scope | `05-approve-help-center-scope` |
| 6  | Scope Pendo               | `06-scope-pendo`               |
| 7  | Approve microcopy scope   | `07-approve-microcopy-scope`   |
| 8  | Create help center PR     | `08-create-help-center-pr`     |
| 9  | Publish to knowledge base | `09-publish-to-knowledge-base` |

## Sequencing and manual-trigger checkpoints

Task 1 (Intake) runs all four intake steps in sequence, then **stops and waits for a
manual trigger**:

- **After Task 1 (Intake):** a TW reviews the full intake output (Categorization, Context,
  Preliminary scope, and Structural review) and makes any necessary adjustments.

Task 2 (Approve intake) runs all four approve-intake steps in sequence with no stop.

All other tasks (3–9) are triggered individually unless the prompt says otherwise.

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
### TW Agent status

- [TO DO] 1 - Intake
  - [TO DO] 1a - Categorization
  - [TO DO] 1b - Context
  - [TO DO] 1c - Preliminary scope
  - [TO DO] 1d - Structural review
- [TO DO] 2 - Approve intake
  - [TO DO] 2a - Structuring
  - [TO DO] 2b - Cleaning
  - [TO DO] 2c - Working files
  - [TO DO] 2d - Populate children
- [TO DO] 3 - Scope microcopy
- [TO DO] 4 - Scope help center
- [TO DO] 5 - Approve help center scope
- [TO DO] 6 - Scope Pendo
- [TO DO] 7 - Approve microcopy scope
- [TO DO] 8 - Create help center PR
- [TO DO] 9 - Publish to knowledge base
```

After completing any task (or group of tasks in one run), immediately update this section:

- Convert each completed step line to `[DONE]` and strike it through with `~~...~~`
- For Tasks 1 and 2, also strike through and mark `[DONE]` each completed sub-task line
- When all sub-tasks of Task 1 or Task 2 are done, mark the parent line `[DONE]` as well
- Leave all remaining steps as `[TO DO]`
- Keep step numbering unchanged
- Keep this section at the top of the description after each update

## Response format

End every task response with a single line:

`Last: [task name] / Next: [task name or "Stop — manual trigger"]`
