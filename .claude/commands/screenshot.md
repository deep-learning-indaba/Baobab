Take a screenshot of a page in the Baobab dev app and critically review it for visual defects.

**Usage:** `/screenshot <path>` e.g. `/screenshot /test2021/programmeEditor`

## Setup

```bash
# Install playwright package if missing
# macOS can partly clean /tmp, leaving the directory without package.json, so check that it resolves
(cd /tmp/pw_test 2>/dev/null && node -e "require.resolve('playwright')" 2>/dev/null) || (mkdir -p /tmp/pw_test && cd /tmp/pw_test && rm -rf node_modules/playwright node_modules/playwright-core && npm install playwright)

# Install Chromium if missing
ls /tmp/pw_browsers/chromium_headless_shell-* 2>/dev/null || PLAYWRIGHT_BROWSERS_PATH=/tmp/pw_browsers npx --prefix /tmp/pw_test playwright install chromium
```

## Script template

Use the shared session helper, which logs in, pre-sets the cookie-consent cookie so the banner never covers the page, and captures the bottom of the inner scroll container when the page overflows it:

```js
const { chromium } = require('playwright');
const { openSession } = require('<repo>/.claude/skills/verify-feature/baobab_pw.js');
(async () => {
  const s = await openSession(chromium, { shotDir: '/tmp/pw_test/shots' });
  try {
    await s.goto('$ARGS');
    console.log('Final URL:', s.page.url());
    console.log(await s.shot('screenshot'));
    console.log(JSON.stringify(s.report()));
  } finally {
    await s.close();
  }
})();
```

Replace `<repo>` with the output of `git rev-parse --show-toplevel`.

**Credentials** come from environment variables, set locally in `.claude/settings.local.json` under `env`:

| Variable | Account |
| --- | --- |
| `BAOBAB_TEST_EMAIL` / `BAOBAB_TEST_PASSWORD` | Site admin (default login) |
| `BAOBAB_TEST_USER_EMAIL` / `BAOBAB_TEST_USER_PASSWORD` | Ordinary user, no roles |

To view a page as the ordinary user, pass `{ email: process.env.BAOBAB_TEST_USER_EMAIL, password: process.env.BAOBAB_TEST_USER_PASSWORD }` to `openSession`. For a logged-out page, pass `{ login: false }`.

Use `{ viewport: { width: 390, height: 844 } }` for a mobile check.

Run with:
```bash
cd /tmp/pw_test && PLAYWRIGHT_BROWSERS_PATH=/tmp/pw_browsers node <script>.js
```

Run the script from inside `/tmp/pw_test` (via `-e` inline, or a file saved directly in that directory) — Node resolves `require('playwright')` relative to cwd, so a script written to the scratchpad dir and run from there fails with `MODULE_NOT_FOUND`. Don't copy it over after the fact; write/run it there the first time.

## Screenshotting popups, modals, and other `position: fixed` overlays

Trigger the interaction (click, hover, etc.) and screenshot **without** `fullPage: true` — use a plain `await page.screenshot({ path: ... })`. A fixed-position element renders once at its viewport location; a full-page screenshot stretches the capture to the whole scrollable page height while the fixed element stays pinned to where the viewport was, which reads as if the overlay is cut off or floating over unrelated content. Viewport-only capture is what actually reflects what a user sees.

When the interaction is a click on a list of repeated cards (e.g. one of several parallel/concurrent items), target the element that matches the scenario under test, not just `.first()` — e.g. `locator(...).nth(1)` for "a parallel session" rather than the first card in the list, which is often a different, non-representative case (a single keynote, an empty state, etc.). Picking the right target the first time avoids a second full run.

## Verifying navigation / redirects

If the change under test is a conditional redirect (not just layout), don't rely on the screenshot alone — add `console.log('Final URL:', page.url())` right before the screenshot call. Compare it against the expected path to confirm the redirect actually fired (or correctly didn't).

To exercise a redirect that depends on specific data (e.g. an event starting "soon"), temporarily edit the relevant row via `docker-compose exec -T db psql -U docker -d docker` (see root CLAUDE.md for DB access), re-run the script, then revert the row immediately after confirming.

## Critical review checklist

After taking the screenshot(s), read each image and explicitly check every item below. Do **not** declare success until each is addressed.

**Text & content clipping**
- [ ] Is any text cut off mid-word or mid-line at the bottom or right edge of a card/container?
- [ ] Are speaker names, descriptions, or labels hidden by `overflow: hidden` when they should be visible?
- [ ] Do cards with little content look too empty? Do cards with lots of content overflow their box?

**Spacing & margins**
- [ ] Is horizontal padding consistent with peer pages (Review Dashboard, Invoices)? No extra left/right gutters.
- [ ] Is vertical spacing between sections consistent — not too cramped or too airy?
- [ ] Does the page align with the sidebar correctly, or does content bleed under it?

**Layout**
- [ ] Are columns/grids rendering the expected number of columns at 1280px wide?
- [ ] Are parallel/side-by-side elements actually side by side, not stacked?
- [ ] Are sticky headers/toolbars visible and not obscuring content beneath them?

**Typography**
- [ ] Are all labels, headings, and body text rendering as text (not as icon codepoints like "calendar_today")?
- [ ] Are font sizes visually correct relative to each other?

**Interactive state**
- [ ] Are buttons, chips, and inputs visually distinct and clearly styled?
- [ ] Is the active/selected state (day chip, filter) visually obvious?

**Flags to report:** For each issue found, describe: what is wrong, where it appears, and what the fix likely is. Only report "looks good" if every checkbox is genuinely clear.
