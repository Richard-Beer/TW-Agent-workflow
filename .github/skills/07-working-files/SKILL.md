---
name: 07-working-files
description: 'Task 7 of the Tech Writer workflow. Use to create the Google Drive working folder and per-deliverable working files (Sheets/Docs) for a Cin7 Jira issue via drive.py, and add a Working files section to the issue description.'
argument-hint: 'Jira issue ID'
---

# Task 7 — Working files

Using `drive.py` (see the script and path conventions in the repository instructions),
create a folder named after the issue key inside the TW team Google Drive folder
(`1YhXSSv6EPb_-td-bajDE2ev3P-RLZNNL`):

```
cd "c:\Users\RichardBeer\Repos\TW Tech Writer agent\Scripts\google_drive"
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
a hyperlink) until the branch is created in **Task 11 — Approve scope**.
