---
name: 02-approve-intake
description: 'Task 2 of the Tech Writer workflow. Use to apply the Structuring advice for a Cin7 Jira issue, clean the description, create Google Drive working files, and populate child issue descriptions. Runs straight through without stopping.'
argument-hint: 'Jira issue ID'
---

# Task 2 — Approve intake

Run the following four steps in sequence without stopping between them.

---

## Step 2a — Structuring

Apply the restructuring advice from the **Structuring advice** section — for example,
promoting the issue to an epic, creating child issues, or adding subtasks as recommended.

### Child issue names

When creating child issues, use exactly these names — no parent issue key prefix, no other
identifier:

| Deliverable | Child issue name |
|---|---|
| Microcopy | `Microcopy` |
| Help center | `Help center` |
| Pendo guides | `Pendo` |
| EAP | `EAP` |

### How to create child issues

Child issues are always subtasks of the current story-level issue. For each in-scope
deliverable, call `jira_create_issue` with:

- `project_key`: `OTW`
- `issue_type`: `Subtask`
- `summary`: the child issue name from the table above (e.g. `Help center`)
- `additional_fields`: `{"parent": "<current issue key>"}` — the key of the issue you
  are currently processing (e.g. `OTW-1234`)

Do not set a description when creating the child issue — descriptions are populated in
Step 2d.

### How to set parent assignments

To assign or update the parent on an existing issue, call `jira_update_issue` with:

- `issue_key`: the issue to reparent
- `additional_fields`: `{"parent": "OTW-XXXX"}` — the target parent issue key

### Parent epic assignment

After structuring, set the parent epic for the issue (or new epics/stories created) based
on the issue's category (determined in Task 1):

**If the issue was promoted to an epic:**
- Assign the new epic's parent to:
  - `OTW-1616` — if category is **Release**
  - `OTW-1617` — if category is **Foundations** or **Enablement**
- Assign each new child story's parent to the new epic (set at creation time via
  `additional_fields: {"parent": "<new epic key>"}` in `jira_create_issue`).

**If the issue stays as a story:**
- Assign the story's parent epic to:
  - `OTW-1862` — if category is **Release**
  - `OTW-1619` — if category is **Foundations**
  - `OTW-1633` — if category is **Enablement**

The category is visible on the issue (set during Task 1 as the issue type: Feature Request
= Release, Doc Request = Foundations, Task = Enablement).

Once you complete the Structuring step, continue to Step 2b.

---

## Step 2b — Cleaning

Update the issue description as follows:

- Remove the **Request (original)** section
- Rename **Request (refined)** to **Requirements**
- Remove the **Structuring advice** section (the restructuring has now been applied)

Once you complete the Cleaning step, continue to Step 2c.

---

## Step 2c — Working files

Using `drive.py` (see the script and path conventions in the repository instructions),
create a folder named after the issue key inside the TW team Google Drive folder
(`1YhXSSv6EPb_-td-bajDE2ev3P-RLZNNL`):

```
cd "c:\Users\RichardBeer\Repos\TW-Tech-Writer-agent\Scripts\google_drive"
python -B drive.py create-folder "OTW-XXXX" --parent 1YhXSSv6EPb_-td-bajDE2ev3P-RLZNNL
```

For each in-scope deliverable identified in the **Requirements** section, create a working
file inside that folder, named in the format `OTW-XXXX - [Deliverable type]` where
Deliverable type matches the deliverable name from the **Requirements** section (e.g.
`Microcopy`, `Pendo guides`, `EAP`).

Do not create a Help center Google Doc. If Help center is in scope, add a placeholder line
to the **Working files** section: `Help center (markdown KB repo)`.

Use `create-sheet` for the **Microcopy** deliverable:

```
python -B drive.py create-sheet "OTW-XXXX - Microcopy" --parent <folder_id>
```

Use `create-doc` for all other Google Drive deliverables:

```
python -B drive.py create-doc "OTW-XXXX - [Deliverable type]" --parent <folder_id>
```

Add a new **Working files** section to the issue description. Use markdown hyperlinks so
that labels are inline and clickable in Jira.

```
### Working files

- [Microcopy](https://docs.google.com/spreadsheets/d/<sheet_id>/edit)
- Help center (markdown KB repo)
- [Pendo guides](https://docs.google.com/document/d/<doc_id>/edit)
```

Include only lines for in-scope deliverables. Keep the Help center line as plain text (not
a hyperlink) until the branch is created in **Task 5 — Approve help center scope**.

Once you complete the Working files step, continue to Step 2d.

---

## Step 2d — Populate children

For each child issue, add the related requirement and working file reference to the child
issue's description.

### Identify the deliverable

Each child issue is named after the deliverable it covers (e.g. `Help center`,
`Microcopy`). Use this name to locate:

- The matching requirement from the parent issue's **Requirements** section
- The matching working file entry from the parent issue's **Working files** section

### Update the child description

Set the child issue's description to the following:

```
### Requirements

[Requirement text from parent's Requirements section for this deliverable]

### Working file

[Working file reference from parent's Working files section for this deliverable]
```
