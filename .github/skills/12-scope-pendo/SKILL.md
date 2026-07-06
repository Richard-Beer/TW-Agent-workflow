---
name: 12-scope-pendo
description: 'Task 12 of the Tech Writer workflow. Use to produce a strategic Pendo guide plan for a Cin7 Jira issue using the Pendo model, and add a Pendo strategy section to the issue description. Strategic only — no final guide copy.'
argument-hint: 'Jira issue ID'
---

# Task 12 — Scope Pendo

Read the **Requirements** section from the issue's description, specifically the Pendo
guides entry. Based on the context of the issue and those requirements, produce a Pendo
strategy.

Keep this step strategic and implementation-oriented:

- Focus on intent, structure, and placement
- Do not draft final guide copy
- Keep details general and simple when evidence is limited
- If a required detail cannot be confirmed, write `Unknown` instead of guessing
- Describe audience in practical terms (role + situation), not technical segmentation-rule
  syntax

Add a new section called **Pendo strategy** to the issue description. Use the following
template:

```
**Pendo strategy**

**High-level summary**

**Goal:** [One-sentence summary of what the full guide set should achieve]

**Strategy:** [One of the three strategies from the Pendo model]

**Guide areas:** [Use navigation labels from the product model]

**Audience:** [Who should see the guides, in practical terms]

**Guide map**

**Guide count:** [Total number of individual guides planned]

- **Guide:** [Guide name]
   - **Type:** [Guide type from the Pendo model]
   - **Audience:** [Effective audience for this guide]
   - **Trigger:** [What event/action causes this guide to appear]
   - **Location:** [Navigation label from the product model; `Unknown` if not confirmed]
   - **Selector:** [Primary target selector; `Unknown` if not confirmed]
   - **Tone/language:** [Brief style summary, not actual microcopy]
   - **Links to other guides:** [Entry/follow-up/fallback/mutually exclusive — include only when Strategy is "Multiple guides with structural links"]

   - **Steps:** [Only for Multi-step guides]
      1. [Step purpose] — [Location] — [Selector]
      2. [Step purpose] — [Location] — [Selector]
      [Add more steps as needed]
      [Note only meaningful differences between steps if this is clearer than repeating full detail]

**Notes:** [Any caveats, dependencies, or open questions]
```

Adjust the number of guides and steps as needed. Omit the **Notes** line if there is
nothing to note.

Before publishing the description, run this quality check internally (do not add this
checklist to the issue description):

- [ ] Guide count matches the number of listed guides
- [ ] Strategy is one of the three types defined in the Pendo model
- [ ] Every guide type matches a type defined in the Pendo model
- [ ] Guide areas and Location values use navigation labels from the product model
- [ ] Every guide includes type, audience, trigger, location, selector, and tone/language
- [ ] Multi-step guides include a step sequence
- [ ] Links to other guides is included only when Strategy is "Multiple guides with structural links"
- [ ] Uncertain details are marked as `Unknown`
- [ ] No final guide copy is drafted
