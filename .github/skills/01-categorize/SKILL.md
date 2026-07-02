---
name: 01-categorize
description: 'Task 1 (AKA Begin) of the Tech Writer workflow. Use to categorize a Cin7 Jira issue as Release, Foundations, or Enablement, set its issue type, and attempt to set the Due date. First step in the sequence.'
argument-hint: 'Jira issue ID'
---

# Task 1 — Categorization (AKA Begin)

Read only the issue, its children, and any linked issues to categorize the issue. The
available categories are:

- **Release** — issues that likely deliver help center or EAP articles, microcopy, or
  Pendo guides to support a product release
- **Foundations** — issues that likely deliver help center or EAP articles, microcopy, or
  Pendo guides not related to a release
- **Enablement** — issues that likely deliver internal enablement (e.g. tooling, process,
  or team capability work)

**If you cannot determine the category**, set the issue type to `Triage` and add the
following warning to the description:

> AI Tech Writer failed to categorize

**If the category is Release but there is no linked issue**, set the issue type to
`Triage` and add the following warning to the description:

> AI Tech Writer attempted to categorize this issue as Release, but no related issue was found

**Otherwise**, set the issue type as follows:

| Category    | Issue type      |
|-------------|-----------------|
| Release     | Feature Request |
| Foundations | Doc Request     |
| Enablement  | Task            |

If and only if you can categorize the issue, proceed to **Task 2 — Context**.

After categorization, attempt to set the issue Due date using the **Due date handling**
rules in the repository instructions.
