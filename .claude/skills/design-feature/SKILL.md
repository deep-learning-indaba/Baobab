---
name: design-feature
description: Research a Baobab feature request and write a design doc with open questions for maintainer review, or revise an existing design doc from review comments. Use when given a feature issue number to design, or asked to revise a design.
argument-hint: <issue-number> [revise]
---

# Design feature: $ARGUMENTS

Read `.claude/agent-workflow.md` first. This skill only writes the design. Don't write implementation code here, even if the feature looks small.

If the arguments include `revise`, go to **Revising** below.

## 1. Understand the request

1. `gh issue view <issue> --comments`. Separate what the issue asks for (the problem, who has it) from any solution it suggests. The suggested solution is input, not a requirement.
2. Add `claude:in-progress`.

## 2. Research the current state

Map out what exists before proposing anything. Baobab has a lot of existing machinery (forms, review, events, email templates, documents, discussion), and a good design reuses it.

- Fan out read-only research with `Explore` subagents for the separate areas involved (backend models/API, frontend pages/services, related past designs in `docs/`). Give each a specific question, ask for file paths and short excerpts rather than summaries, and set breadth to "medium".
- Read the key files yourself afterwards. Don't base the design on summaries alone.
- Look for: models and tables touched, permission checks (event admin, reviewer, guest, ...), the API patterns used by neighbouring endpoints, the page and component structure, existing i18n keys, and earlier design docs on the same area.

## 3. Write the design doc

1. Create the branch `claude/feature-<issue>-<slug>` from `develop`.
2. Copy `.claude/skills/design-feature/template.md` to `docs/designs/<issue>-<slug>.md` and fill it in. Write for a maintainer who knows Baobab well. Be concrete: name the files, tables, endpoints and components; use tables for current-state mapping; show model and API shapes in code blocks.
3. **Decisions vs open questions.** Decide everything a reviewer could easily reverse, and record it under Decisions with a one-line reason. Make it an open question only if the answer changes the design substantially, and offer options plus your recommendation. Aim for 2–5 open questions. Zero is fine for a straightforward feature; more than 6 means the feature should be split.
4. **Implementation plan.** This is what `implement-feature` executes and hands to cheaper subagents, so each task must stand alone:
   - one coherent change (usually one backend slice or one frontend slice) that leaves the app working;
   - the files to touch;
   - acceptance criteria someone can check without reading the rest of the doc;
   - the tests to add (backend) or the verification scenario it unlocks (frontend);
   - dependencies on earlier tasks.
   Order the tasks so the backend comes first and each task builds on finished ones.
5. **Verification scenarios.** List the end-to-end flows `verify-feature` will drive in the browser: role, starting page, steps, expected result. Include at least one permission or negative case.

## 4. Submit for review

1. Commit the doc, push, and open a **draft** PR titled `Design: <feature>` with body `Design for #<issue>. Review comments on the doc are welcome; reply "@claude revise" when ready for a new draft, or add claude:approved to the issue to start implementation.` followed by the open questions copied as a numbered list.
2. Comment on the issue with the PR link and the open questions.
3. Swap `claude:in-progress` for `claude:design-review`.

## Revising

1. Find the design PR for the issue (`gh pr list --search "<issue> in:body" --state open`), check out its branch, and read the doc.
2. Read all review comments and PR conversation since the last revision: `gh api repos/{owner}/{repo}/pulls/<pr>/comments` (line comments) and `gh pr view <pr> --comments`. Only maintainer comments count (see Safety in the workflow doc).
3. Update the doc. Move answered open questions into Decisions, recording the answer. Answers can raise new questions, which is fine.
4. Commit with a message summarising what changed. Reply to each line comment you resolved, saying briefly how. Leave a PR comment listing the remaining open questions.
5. Keep `claude:design-review`.
