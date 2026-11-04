---
name: verify-feature
description: Verify a Baobab feature or fix end to end by driving the running app in a headless browser, through each scenario as the relevant user role, reviewing screenshots critically, and writing a pass/fail report. Use after implementing a feature or UI fix, or when asked to test a flow in the app.
argument-hint: <design-doc-path or description of the scenarios>
---

# Verify: $ARGUMENTS

This checks behaviour the way a user experiences it. Frontend changes have no unit tests, so this is the main evidence that the UI works. Be a sceptical tester, not a demo: you're looking for what's broken.

## Setup

- **The stack must be running.** Locally that's your dev stack: `docker-compose ps` shows `web` (port 5000) and `webapp` (port 8080). Headless runs start a fresh one with `scripts/agent/start-env.sh` before you begin. That script runs migrations, seeds test data and installs Playwright; run it yourself if `curl -s -o /dev/null -w "%{http_code}" http://localhost:8080` doesn't return 200.
- **Seed data** comes from `flask seed-agent` (`api/app/utils/seed_agent.py`). It creates the event `agent-test` ("Agent Test Event", always open for applications and reviews, new form system, en and fr), with an application form and a linked review form, plus one account per role, all with the password in `BAOBAB_TEST_PASSWORD`:

| Role (`as:`) | Account | What they have |
| --- | --- | --- |
| `admin` (default) | `claude-admin@baobab.test` | Site admin |
| `user` | `claude-user@baobab.test` | No roles; for permission and negative cases |
| `event-admin` | `claude-event-admin@baobab.test` | Event admin of `agent-test` |
| `reviewer` | `claude-reviewer@baobab.test` | Reviewer of `agent-test`, with one assigned review (not started) |
| `applicant` | `claude-applicant@baobab.test` | A submitted application to `agent-test` |
| `guest` | `claude-guest@baobab.test` | Confirmed invited guest of `agent-test`, so the event app pages are available |

  Prefer `agent-test` over older events for new scenarios. If a scenario needs data the seed doesn't have (a second applicant, a tag, a submitted review), create it through the app's own API or UI. Fall back to `psql` (see `.claude/CLAUDE.md`), and record every row you add or change so you can revert it at the end.
- Playwright lives in `/tmp/pw_test`. Install it if missing, as described in the Setup section of `.claude/commands/screenshot.md`. Write and run scripts **inside `/tmp/pw_test`** so `require('playwright')` resolves.
- Use the session helper `.claude/skills/verify-feature/baobab_pw.js`. It sets the cookie-consent cookie, logs in through the API as a seeded role, and records console errors and failed API calls. Require it by absolute path:

```js
const { chromium } = require('playwright');
const { openSession } = require('<repo>/.claude/skills/verify-feature/baobab_pw.js');
(async () => {
  const s = await openSession(chromium, { as: 'event-admin', shotDir: '/tmp/pw_test/shots/<run>' });
  try {
    await s.goto('/agent-test/someFeature');
    await s.page.getByRole('button', { name: 'Save' }).click();
    await s.settle();
    await s.shot('01-after-save');
    console.log(JSON.stringify(s.report(), null, 2));
  } finally {
    await s.close();
  }
})();
```

  Other options: `{ email, password }` for any other account, `{ login: false }` for logged-out pages, `{ viewport: { width: 390, height: 844 } }` for mobile, and `baseUrl` / `apiUrl` (or `BAOBAB_WEB_URL` / `BAOBAB_API_URL`) when the app isn't on ports 8080 and 5000.

### What can't be checked in a seeded environment

- **Email** is never delivered (SMTP settings are placeholders). Check that the right message was queued instead: query the `outbox_message` table (recipient, subject, status) after the action.
- **Google Docs/Drive** (document generation, invitation letters) needs real Google credentials, which only a developer's local `docker-compose.override.yml` has. In headless runs, mark these scenarios ⚠️ Not run and say why.
- **Stripe payments** can't be completed. Verify up to the point of redirecting to Stripe.

## For each scenario

1. Write down the expected result before running it.
2. Drive it with real interactions (clicks, typing, selecting), not by calling the API directly. API calls are only for setting up data. Use role- or text-based locators (`getByRole`, `getByLabel`, `getByText`) over CSS classes.
3. Screenshot every meaningful state: the starting page, after each key action, and the end state. Use `fullPage: true` for pages and viewport shots for modals and other fixed overlays (see the screenshot command for why).
4. Check more than the screenshot:
   - the final URL, for navigation and redirects;
   - `s.report()`: any console error or API response of 400 or above during a scenario that should succeed is a failure, unless you can explain it;
   - persistence: reload the page, or read the record back from the API, to confirm a save really saved.
5. **Look at every screenshot** with the Read tool, and go through the checklist in `.claude/commands/screenshot.md`: clipping, spacing, layout, typography, interactive state. Also check that new text is translated (no raw i18n keys like `discussion.reactions.title` on screen).
6. For any screen with new UI, also run at 390×844 (`viewport` option) and check the mobile layout.
7. Run any permission or negative scenario as the restricted user, and confirm both that the UI hides the action and that the API refuses it.

Also run one French-locale pass over new screens (append `?lng=fr` to the URL; the language detector checks the query string first) and check nothing falls back to English.

## Report

Write the report in markdown. Reference screenshots by file name while drafting. When the report is going on GitHub, publish the images and swap in the links:

```bash
scripts/agent/publish-screenshots.sh /tmp/pw_test/shots/<run> issue-<n>/<yyyy-mm-dd>-<slug>
```

This commits them to the `agent-artifacts` branch (never merged) and prints a markdown image link per file. Only publish in headless runs, or locally when the developer asks: the repo is public.

```markdown
## Verification report

**Result:** <n>/<m> scenarios pass · <date> · branch `<branch>` @ `<short sha>`

| # | Scenario | Role | Result | Evidence |
| --- | --- | --- | --- | --- |
| 1 | ... | Event admin | ✅ Pass | 01-start.png, 02-saved.png |
| 2 | ... | Applicant | ❌ Fail | 05-error.png |

### Failures
<for each: steps, expected, actual, screenshot, console/API errors, likely cause and file if known>

### Visual review
<issues from the checklist: what, where, likely fix; or "No issues found" only if every item was checked>

### Mobile and French
<findings>

### Test data changes
<rows added or changed, and confirmation they were reverted>
```

Don't report a pass you didn't observe. If a scenario couldn't be run (missing data, a blocking bug earlier in the flow), mark it ⚠️ Not run and say why.

Before finishing, revert every dev DB change you made.
