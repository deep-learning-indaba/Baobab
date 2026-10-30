---
name: fix-bug
description: Fix a Baobab bug from a GitHub issue - reproduce it with a failing test or a scripted browser run, fix it, verify, and open a PR. Use when given a bug issue number or asked to fix a reported bug.
argument-hint: <issue-number>
---

# Fix bug #$ARGUMENTS

Read `.claude/agent-workflow.md` first; its labels, branch naming, budget and safety rules apply throughout.

## 1. Understand

1. `gh issue view $ARGUMENTS --comments`. Note the reported behaviour, the expected behaviour, the page or endpoint, the user role, and any event or form it happened on.
2. Add the `claude:in-progress` label.
3. Find the code involved. Trace from the page in `webapp/src/pages/` through its service in `webapp/src/services/` to the endpoint in `api/app/`. Read the code before forming a theory.
4. If the report is too vague to say what "fixed" means, ask (see "Headless vs interactive" in the workflow doc) and stop.

## 2. Reproduce, before changing any code

Pick the cheapest reproduction that actually shows the bug:

- **Backend logic or API bug**: write a pytest test next to the existing tests for that module, asserting the *expected* behaviour. Run it and confirm it fails for the reason in the report, not because of a typo or fixture problem.
- **Frontend-only bug** (rendering, layout, client-side logic): write a Playwright script using the helper in `.claude/skills/verify-feature/baobab_pw.js` that walks the steps in the report and captures the broken state as a screenshot, plus the URL and any console errors.
- **Both**: do both.

If you can't reproduce the bug, don't fix it blind. Report what you tried, what you observed, and what extra information would help, then stop with `claude:blocked`.

## 3. Fix

1. Create the branch `claude/bug-<issue>-<slug>` from `develop`.
2. Make the smallest change that fixes the root cause. If the cause is in shared code, check the other callers with grep; the fix must not break them.
3. Follow `.claude/CLAUDE.md`: i18n for any new UI text (en and fr), comment conventions, and CRLF line endings preserved on files that use them.
4. Up to 3 attempts (see Budget in the workflow doc).

## 4. Verify

- Run the reproducing test: it must now pass. Then run the whole test module it lives in, and the module of any other caller you touched.
- For frontend changes, run `pnpm run build` in `webapp/`, then re-run the Playwright reproduction and screenshot the fixed state. Run the `/screenshot` review checklist on it.
- Check `git diff --stat` for unexpected files or whole-file line-ending changes.

## 5. Submit

1. Commit, push, and open a PR against `develop`:

```markdown
Fixes #<issue>

## Cause
<one paragraph: what was wrong and why>

## Fix
<what changed, and why this is the right place to fix it>

## Verification
- Reproduced by: <test name, or Playwright steps>, failing before the fix
- After the fix: <tests run and results; screenshots for UI changes>

## Noticed, not fixed
<related issues spotted, or "None">
```

2. For UI fixes, add before/after screenshots as a PR comment.
3. Comment on the issue with a one-line summary and the PR link. Swap `claude:in-progress` for `claude:pr-review`.
