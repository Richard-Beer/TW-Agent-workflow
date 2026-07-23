---
name: 06-approve-help-center-scope
description: 'Task 6 of the Tech Writer workflow. Use to approve Help center scope for a Cin7 Jira issue — either by publishing scoped articles to a Google Doc working file, or by creating a Help center branch in the TW-Knowledge-bases-markdown repo.'
argument-hint: 'Jira issue ID, then approval type: "Approve and make Google working files" or "Approve and make branch"'
---

# Task 6 — Approve help center scope

Approve the Help center scope for the issue using one of two paths, chosen by the user.

## Inputs

Ask the user for two things before proceeding:

1. **Jira issue key** (e.g. `OTW-1234`)
2. **Approval type** — one of:
   - `Approve and make Google working files`
   - `Approve and make branch`

All other required data is read from the issue description — do not ask for it manually.

## Step 1 — Read the issue

Fetch the issue and identify:

- The **issue key**
- The **product context** — Core or Omni (determines the markdown KB subfolder)

## Step 2 — Read article filenames from the Help center scope table

In the issue description, find the `### Help center scope` section (written by Task 5).
Extract every article title where the **Action** column is **Update** or **Create**. Skip
rows where Action is **Delete**.

Resolve each title to a full file path using the product context:

- Core: `c:\Users\RichardBeer\Repos\TW-Knowledge-bases-markdown\Core\<title>.md`
- Omni: `c:\Users\RichardBeer\Repos\TW-Knowledge-bases-markdown\Omni\<title>.md`

If the `### Help center scope` section is missing or contains no Update/Create rows, add a
`[TW Agent] No scoped articles found in Help center scope table` note to the issue
description and stop.

## Step 3 — Branch on approval type

### Approve and make Google working files

**3a. Ensure the Google Doc exists.**

In the issue description, find the `### Working files` section. Look for the Help center
line.

- If the Help center line is already a **hyperlink** in the form `[Help center](<url>)`,
  extract the Doc ID from the URL using the pattern `/document/d/<DOC_ID>/`.
- If the Help center line is still the plain-text placeholder (`Help center`), **create
  the Google Doc now**:

  First, identify the working folder ID from the `[Working folder](<url>)` line in
  Working files (extract the folder ID from the URL pattern `/folders/<FOLDER_ID>`).

  ```
  cd "c:\Users\RichardBeer\Repos\TW-Agent-workflow\Scripts\google_drive"
  python -B drive.py create-doc "<issue_key> - Help center" --parent <folder_id>
  ```

  Then update the Working files section: replace the plain-text `Help center` line with
  `[Help center](https://docs.google.com/document/d/<doc_id>/edit)`.

  If a **Help center subtask** exists (check sibling subtasks), also update its description's
  **Working file** section with the new hyperlink.

**3b. Publish articles to the Google Doc.**

Run `write-markdown-to-doc` via `drive.py`, passing all resolved file paths in one call:

```
cd "c:\Users\RichardBeer\Repos\TW-Agent-workflow\Scripts\google_drive"
python -B drive.py write-markdown-to-doc <DOC_ID> --files <full_path_1> [<full_path_2> ...]
```

Each article is written to a named tab in the Doc. Files that do not exist on disk
(e.g. Create-action articles not yet drafted) are skipped by `drive.py` automatically.

---

### Approve and make branch

**3a. Create and publish the branch.**

```
cd c:\Users\RichardBeer\Repos\TW-Knowledge-bases-markdown
git checkout master
git pull
git checkout -b <issue_key>
git push -u origin <issue_key>
```

**3b. Update the issue description's Working files section.**

Find the plain-text placeholder line `Help center` and replace it with a link to the new
branch:

`[Help center](https://github.com/Cin7Americas/TW-Knowledge-bases-markdown/tree/<issue_key>)`

If a **Help center subtask** exists (check sibling subtasks), also update its description's
**Working file** section with the new branch link.
