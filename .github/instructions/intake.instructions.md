---
description: "Local instruction sheet for the Intake agent. Loaded explicitly by the Intake agent — do not load in any other agent."
---

# Intake — local instructions

This file contains instruction content specific to the Intake agent. It supplements the
shared conventions in `.github/copilot-instructions.md`.

## Input

The user provides a URL to a PDF analysis document.

## Workflow

1. **Fetch the document** — retrieve the document's text content using the method that matches the input:
   - **Google Doc URL** (URL contains `docs.google.com/document`) — run
     `python -B drive.py read-doc <URL>` from
     `c:\Users\RichardBeer\Repos\TW Tech Writer agent\Scripts\google_drive`
     and use the printed output as the document content.
   - **Any other URL** — use the `fetch_webpage` tool with the provided URL.
2. **Analyse the document** — read the full content and identify:
   - The strategic themes or parallel workstreams the document describes.
   - Every distinct TW-relevant task (help center, microcopy, in-app guidance, documentation,
     onboarding content, tooltips, etc.).
   - Non-TW work (engineering, product, analytics) — note it briefly but do not include it
     in the stories.
   - Whether any TW task is large enough to warrant an epic with child stories rather than a
     single story.
3. **Produce structured output** — write the output using the template below, then stop and
   wait for the user to review. Do not create any Jira issues unless explicitly asked.

## Output template

Produce output in exactly this structure. Annotations in square brackets describe what to
derive from the document; remove the annotations from your actual output.

```markdown
## Strategic objectives (from the document)
[One or two sentences framing the overall goal of the document's recommendations.]
[Then describe the parallel tracks or workstreams — always include this section even if
there is only one track. Use a bullet list of bold track names with a short description each.
Finish with a sentence stating where the TW work sits across those tracks.]

---

## Stories — preliminary definitions
[One block per TW story, separated by horizontal rules. If a story is large enough to
warrant an epic, say so explicitly and list its proposed child stories beneath it.
Each story uses this exact format:]

**Story N — [Short title]**

- **Aim:** [One sentence — the goal of this story.]
- **Method:** [Two to four sentences — how the work will be done: what sources to consult,
  what analysis to perform, what the output looks like.]
- **Deliverables:** [One sentence listing the concrete output(s).]
- **Success metric:** [One sentence — how you would know this story is complete and
  sufficient.]

---
[Repeat for each story]

## Non-TW work
[A brief bullet list of engineering, product, or analytics recommendations from the
document that fall outside TW scope. One line each — title and one-sentence description.
Omit this section entirely if there is no non-TW work.]
```
