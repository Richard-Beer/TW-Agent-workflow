---
name: 07-create-help-center-pr
description: 'Task 7 of the Tech Writer workflow. Use to open a pull request for Help center markdown updates in the TW-Knowledge-bases-markdown repo, targeting master from the issue-key branch, listing the changed .md files.'
argument-hint: 'Jira issue ID'
---

# Task 7 — Create help center PR

Create a pull request for Help center markdown updates in `TW-Knowledge-bases-markdown`.

## Steps

1. Read the issue to identify the issue key (e.g. `OTW-1234`).
2. Use the markdown knowledge base repo:
   - `c:\Users\RichardBeer\Repos\TW-Knowledge-bases-markdown`
3. Ensure the branch exists and is up to date with remote:

   ```
   cd c:\Users\RichardBeer\Repos\TW-Knowledge-bases-markdown
   git checkout <issue_key>
   git pull
   ```

4. List changed markdown files against `master`:

   ```
   git diff --name-only master...<issue_key>
   ```

5. Create a pull request targeting `master`:
   - **Title:** `<issue_key>: Help center updates`
   - **Body:** A list of modified and created `.md` files from the diff output. If any new
     articles were created, note that they may need TOC entries added manually.

Do not run any Google Drive conversion commands in this task.
