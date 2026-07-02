---
name: 02-context
description: 'Task 2 of the Tech Writer workflow. Use to gather background from a Cin7 Jira issue, its children, and linked issues, then write a Context description using the Release or Foundations/Enablement template. Stops and waits after completion.'
argument-hint: 'Jira issue ID'
---

# Task 2 — Context

Read the issue, its children, any linked issues, and those linked issues' children to
determine relevant background information.

## Handling the existing description

Before writing anything, check whether the issue already has a description:

- If it does, preserve the existing description at the bottom, separated from the new
  content by a line of five stars: `*****`
- Write the new description entirely above this separator, starting from scratch
- Ensure the **TW Agent status** section exists at the top of the new description and
  reflects current completion state
- Consider the existing description as context when writing the new description — any
  relevant information from it should be reflected above the separator
- Having the same information in both the new and original descriptions is intentional;
  the original (below the stars) will be deleted manually after review

## Templates

Add the gathered background information to the issue description using the appropriate
template:

**Release**
- Summary of release (2–3 sentences describing the release and its rationale)
- UX change summary (high-level; likely impact on the user experience, such as new pages,
  new or changed UI elements, and so on)
- Request (original) (explicit Technical Writing requests only — do not infer)

**Foundations and Enablement**
- UX change summary (high-level; the underlying issue or opportunity and expected
  user-visible impact)
- Request (original) (explicit Technical Writing requests only — do not infer)

Once you complete the Context, **stop and wait**.

<!-- A TW reviews the Categorization and Context and makes any necessary adjustments. A TW must manually trigger the next tasks. -->
