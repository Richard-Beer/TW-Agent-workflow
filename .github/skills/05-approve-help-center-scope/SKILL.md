---
name: 05-approve-help-center-scope
description: 'Task 5 of the Tech Writer workflow. Use to approve Help center scope for a Cin7 Jira issue — either by publishing scoped articles to a Google Doc working file, or by creating a Help center branch in the TW-Knowledge-bases-markdown repo.'
argument-hint: 'Jira issue ID, then approval type: "Approve and make Google working files" or "Approve and make branch"'
---

# Task 5 — Approve help center scope

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

## Step 2 — Read article filenames from the Scope table

In the issue description, find the `### Scope` section (written by Task 4). Extract every
article title where the **Action** column is **Update** or **Create**. Skip rows where
Action is **Delete**.

Resolve each title to a full file path using the product context:

- Core: `c:\Users\RichardBeer\Repos\TW-Knowledge-bases-markdown\Core\<title>.md`
- Omni: `c:\Users\RichardBeer\Repos\TW-Knowledge-bases-markdown\Omni\<title>.md`

If the `### Scope` section is missing or contains no Update/Create rows, add a
`[TW Agent] No scoped articles found in Scope table` note to the issue description
and stop.

## Step 3 — Branch on approval type

### Approve and make Google working files

**3a. Read the Google Doc URL from Working files.**

In the issue description, find the `### Working files` section. Look for the Help center
line. It must be a **hyperlink** in the form `[Help center](<url>)`.

If the Help center line is still the plain-text placeholder (`Help center (markdown KB repo)`),
add a `[TW Agent] Missing Help center Google Doc link in Working files` note to the issue
description and stop.

**3b. Extract the Doc ID** from the URL using the pattern `/document/d/<DOC_ID>/`.

**3c. Publish articles to the Google Doc.**

Run `write-markdown-to-doc` via `drive.py`, passing all resolved file paths in one call:

```
cd "c:\Users\RichardBeer\Repos\TW Tech Writer agent\Scripts\google_drive"
python -B drive.py write-markdown-to-doc <DOC_ID> --files <full_path_1> [<full_path_2> ...]
```

Each article is written to a named tab in the Doc. Files that do not exist on disk
(e.g. Create-action articles not yet drafted) are skipped by `drive.py` automatically.

No Jira description update is needed for this path — the Working files section already
contains the hyperlink.

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

Find the plain-text placeholder line `Help center (markdown KB repo)` and replace it
with a link to the new branch:

`[Help center](https://github.com/Cin7Americas/TW-Knowledge-bases-markdown/tree/<issue_key>)`
