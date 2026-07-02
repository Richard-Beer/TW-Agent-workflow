---
name: 08-populate-children
description: 'Task 8 of the Tech Writer workflow. Use to copy the matching Requirement and Working file reference from a parent Cin7 Jira issue into each child issue''s description, keyed by the deliverable the child covers.'
argument-hint: 'Jira issue ID'
---

# Task 8 — Populate children

For each child issue, add the related requirement and working file reference to the child
issue's description.

## Identify the deliverable

Each child issue is named after the deliverable it covers (e.g. `Help center`,
`Microcopy`). Use this name to locate:

- The matching requirement from the parent issue's **Requirements** section
- The matching working file entry from the parent issue's **Working files** section

## Update the child description

Set the child issue's description to the following:

```
**Requirements**

[Requirement text from parent's Requirements section for this deliverable]

**Working file**

[Working file reference from parent's Working files section for this deliverable]
```
