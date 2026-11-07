---
name: implement-feature
description: Implement an approved Baobab design doc by orchestrating implementer and verifier subagents task by task, reviewing each result, then verifying end to end and opening the PR for review. Use when a feature issue has an approved design and implementation should start.
argument-hint: <issue-number>
---

# Implement feature #$ARGUMENTS

Read `.claude/agent-workflow.md` first. You are the orchestrator: you plan, delegate, review and integrate. The `implementer` and `verifier` subagents (Sonnet) do the bulk of the writing and the browser work; `log-triage` (Haiku) condenses long outputs. Keep your own context for judgment: reading diffs, checking them against the design, deciding what comes next.

## 1. Load the approved design

1. `gh issue view $ARGUMENTS --comments` and confirm the issue has `claude:approved`. If it doesn't, stop.
2. Find the design PR and check out its branch `claude/feature-<issue>-<slug>`. Rebase it on `develop` if `develop` has moved and nobody has pushed implementation commits yet.
3. Read the design doc in `docs/designs/` in full, plus the maintainer comments on the PR. Anything a reviewer said that isn't yet reflected in the doc counts as part of the design.
4. If an open question is still unanswered, or an answer contradicts the plan, don't guess: ask and stop (see "Headless vs interactive").
5. Swap `claude:design-review` for `claude:in-progress`.

## 2. Check the plan is delegable

For each task in the Implementation plan, check it has files, acceptance criteria and tests. Fill small gaps yourself, then commit the updated doc with the message "Refine implementation plan". If the plan is substantially wrong (missing layer, wrong model), stop and ask: that's a design change the maintainer should see.

## 3. Execute tasks one at a time

All backend tests run in the single `web` container that mounts the main checkout, so tasks run **sequentially on the feature branch**. Don't use worktrees or parallel implementers.

For each task, in order:

1. **Delegate** to the `implementer` subagent. The prompt must stand alone, because the subagent starts cold:
   - the design doc path, plus the task's section copied in verbatim;
   - what earlier tasks produced that this one builds on (files, function names, endpoints), in a few lines;
   - any decisions from the doc that affect this task;
   - "Commit when done; report files changed, tests added and their results, and anything you couldn't resolve."
2. **Review** the result yourself:
   - `git diff <before>..HEAD` and read it against the acceptance criteria;
   - check the conventions in `.claude/CLAUDE.md`: i18n (en and fr), tests for each new endpoint (including permission cases), comment style, no CRLF churn;
   - re-run the task's tests yourself. Send long output to `log-triage` rather than reading it whole.
3. **Accept** the task, or send it back to the same `implementer` (SendMessage) with specific, numbered problems. After 2 review rounds on one task, finish it yourself if the remaining gap is small; otherwise stop and report.
4. Track the task's status in your todo list. Never start a task whose dependencies aren't accepted.

Total delegations are capped at 1.5× the number of planned tasks (see Budget).

## 4. Whole-feature checks

After the last task:

1. Run the backend test modules for every area touched, then `pnpm run build` in `webapp/`.
2. If there is a migration, run `flask db upgrade` against the dev DB (see `.claude/CLAUDE.md`), then check `flask db heads` shows a single head.
3. Delegate end-to-end verification to the `verifier` subagent. Give it the design doc path, the Verification scenarios table, and the list of pages changed. Ask it to follow the `verify-feature` skill and return its report.
4. Read the report and look at every screenshot it cites yourself. For each problem, either fix it via an `implementer` round, or list it as a known issue if it's out of scope. Re-verify only the scenarios that changed.

## 5. Submit

1. Push. Edit the PR: title `<feature>` (drop the `Design:` prefix), and a body with:

```markdown
Closes #<issue>

Design: docs/designs/<issue>-<slug>.md

## What changed
<bullets by layer: models/migrations, API, frontend, i18n>

## Deviations from the design
<anything built differently from the doc, and why; or "None">

## Testing
- Backend: <modules run, counts>
- Build: pnpm run build ✓
- End-to-end: <n>/<m> scenarios pass — full report below

## Known issues / follow-ups
<or "None">
```

2. Publish the screenshots with `scripts/agent/publish-screenshots.sh` (see "Where things go" in the workflow doc), swap the links into the verifier's report, and post it as a PR comment.
3. Mark the PR ready for review (`gh pr ready`). Comment on the issue with a summary and the PR link. Swap `claude:in-progress` for `claude:pr-review`.
