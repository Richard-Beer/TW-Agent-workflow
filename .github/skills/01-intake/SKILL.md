---
name: 01-intake
description: 'Task 1 of the Tech Writer workflow. Use to run the full intake sequence for a Cin7 Jira issue: categorize the issue, write a Context description, produce a detailed change summary with preliminary deliverable scope, and complete a structural review. Stops and waits after completion for a TW to review.'
argument-hint: 'Jira issue ID'
---

# Task 1 — Intake

Run the following four steps in sequence without stopping between them.

---

## Step 1a — Categorization (AKA Begin)

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

After categorization, attempt to set the issue Due date using the **Due date handling**
rules in the repository instructions.

If and only if you can categorize the issue, continue to Step 1b.

---

## Step 1b — Context

Read the issue, its children, any linked issues, and those linked issues' children to
determine relevant background information.

### Handling the existing description

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

### Templates

Add the gathered background information to the issue description using the appropriate
template:

**Release**
- Summary of release (2–3 sentences describing the release and its rationale)
- UX change (summary) (high-level; likely impact on the user experience, such as new
  pages, new or changed UI elements, and so on)
- Request (original) (explicit Technical Writing requests only — do not infer)

**Foundations and Enablement**
- Problem (summary) (high-level; the underlying issue or opportunity and expected
  user-visible impact)
- Request (original) (explicit Technical Writing requests only — do not infer)

Once you complete the Context, continue to Step 1c.

---

## Step 1c — Preliminary scope

### Stage 1 — Detailed summary

Collect relevant materials from the following sources only:

- The issue, its parent, its children, and any issues linked to any of those
- External files (e.g. Figma designs, Claude prototypes, Confluence pages, Google Drive
  docs) explicitly referenced in or attached to one of the above issues

Using the gathered resources, produce a detailed summary of all UX changes.

The detailed summary covers only changes to the product application itself — that is,
changes a user would encounter while using the software. Record only:

- **Visible changes:** design changes (new/changed/removed pages, buttons, toggles,
  fields, or other interactive UI elements) and microcopy changes (labels, messages,
  tooltips, placeholders)
- **Functional changes:** behind-the-scenes logic changes (e.g. different journals
  created, data mapping changes, workflow changes, new validations)

Do not include TW deliverables in this summary. Content such as help center articles,
Pendo guides, or microcopy documents is produced as a result of this analysis (see
Stage 2) and is not a UX change.

Note explicitly if a design file (Figma or prototype) or microcopy document could not be
found.

The section heading depends on the issue category (determined in Step 1a):

- **Release** → `### UX change (detailed)`
- **Foundations or Enablement** → `### Problem (detailed)`

Add the detailed summary to the issue description in the following format:

```
### [UX change (detailed) or Problem (detailed)]

| Change | Type | Details |
|---|---|---|
| **Visible changes** | | |
| [Element or page] | [Added/Changed/Removed] | [Description] |
| ... | | |
| **Functional changes** | | |
| [Behaviour or logic] | [Added/Changed/Removed] | [Description] |
| ... | | |

**Sources:**
- [List of sources consulted, e.g. Figma file, prototype, microcopy document, linked issue]
- [Note any expected sources that were missing, e.g. "Design file: not found"]
```

### Stage 2 — Deliverable identification

Based on the detailed summary above, identify roughly what deliverables Technical Writing
needs to produce.

Deliverables may include:

- **Help center** — creating, updating, deleting, or otherwise changing help center
  articles, subtopics, or topics
- **Microcopy** — creating, updating, deleting, or otherwise changing UI text
- **Pendo guides** — creating, updating, deleting, or otherwise changing Pendo guides
- **EAP** — creating, updating, deleting, or otherwise changing Early Access Program
  documentation

You are not to plan out the deliverables in detail, but rather identify positively or
negatively whether each of these deliverables is likely to be in scope. The one exception
is that if the Request (original) explicitly calls for a specific deliverable, you should
mark that deliverable as in scope.

Add this information to the issue description in a new section called **Request
(refined)** with a section for in-scope and out-of-scope deliverables. Note explicitly
where the Requirements contradict or go beyond the Request (original) (if any).

Once you complete the Preliminary scope, continue to Step 1d.

---

## Step 1d — Structural review

Based on the Requirements, decide whether this issue type (e.g. epic, story, subtask)
should be changed. Note that stories should be completable within one or two sprints.
Consider what child issues (if any) would be required, which will likely align with the
deliverables identified in the Request (refined).

### Single-deliverable rule

If only **one** deliverable is in scope, recommend **no child issues** — all work should
be managed at the story level. Only recommend child issues when two or more deliverables
are in scope.

### Child issue names

When recommending child issues, use the following default names — use them exactly as
shown, without prefixing the parent issue key or any other identifier:

| Deliverable | Child issue name |
|---|---|
| **Microcopy** | `Microcopy` |
| **Help center** | `Help center` |
| **Pendo guides** | `Pendo` |
| **EAP** | `EAP` |

Add your recommendation to the issue description in a new section called **Structuring
advice**.

Once you complete the Structural review, **stop and wait**.

<!-- A TW reviews the full Intake output (Categorization, Context, Preliminary scope, and Structural review) and makes any necessary adjustments. A TW must manually trigger the next task. -->
