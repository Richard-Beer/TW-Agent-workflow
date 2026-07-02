---
name: 11-approve-scope
description: 'Task 11 of the Tech Writer workflow. Use to create and publish a Help center branch named after the issue key in the TW-Knowledge-bases-markdown repo, and update the Working files section with a link to the branch.'
argument-hint: 'Jira issue ID'
---

# Task 11 — Approve scope

Create and publish a dedicated Help center branch in the markdown knowledge base repo.

## Steps

1. Read the issue to identify:
   - The issue key (e.g. `OTW-1234`)
   - The product context — **Core** or **Omni**
2. Use the markdown knowledge base repo:
   - `c:\Users\RichardBeer\Repos\TW-Knowledge-bases-markdown`
3. Create the branch from `master`:

```
cd c:\Users\RichardBeer\Repos\TW-Knowledge-bases-markdown
git checkout master
git pull
git checkout -b <issue_key>
git push -u origin <issue_key>
```

4. Update the issue description's **Working files** section:
   - Find the plain-text placeholder line: `Help center (markdown KB repo)`
   - Replace it with a link to the branch:
     - `[Help center](https://github.com/Cin7Americas/TW-Knowledge-bases-markdown/tree/<issue_key>)`

Do not create or update any Help center Google Doc in this task.
