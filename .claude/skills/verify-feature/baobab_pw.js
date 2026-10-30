// Playwright session helper for driving the Baobab dev app.
//
// `chromium` is passed in rather than required here: scripts run from
// /tmp/pw_test where Playwright is installed, and a require() from this file
// would resolve relative to the repo instead and fail.

const fs = require('fs');
const path = require('path');

async function openSession(chromium, opts = {}) {
  const {
    baseUrl = process.env.BAOBAB_WEB_URL || 'http://localhost:8080',
    apiUrl = process.env.BAOBAB_API_URL || 'http://localhost:5000',
    email = process.env.BAOBAB_TEST_EMAIL,
    password = process.env.BAOBAB_TEST_PASSWORD,
    viewport = { width: 1280, height: 900 },
    shotDir = '/tmp/pw_test/shots',
    login = true,
  } = opts;

  fs.mkdirSync(shotDir, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport });

  // Without this the cookie banner renders over the bottom of every page and
  // intercepts clicks on anything beneath it.
  await context.addCookies([{ name: 'baobab-cookie-consent', value: 'true', url: baseUrl }]);

  const page = await context.newPage();

  const consoleErrors = [];
  const failedRequests = [];
  let reactWarnings = 0;
  page.on('console', (msg) => {
    if (msg.type() !== 'error') return;
    // React dev-mode warnings (legacy context API, defaultProps, ...) are logged
    // as errors on every page and would bury real failures.
    if (msg.text().startsWith('Warning: ')) {
      reactWarnings += 1;
      return;
    }
    consoleErrors.push({ url: page.url(), text: msg.text() });
  });
  page.on('pageerror', (err) => consoleErrors.push({ url: page.url(), text: String(err) }));
  page.on('response', (resp) => {
    if (resp.url().startsWith(apiUrl) && resp.status() >= 400) {
      failedRequests.push({ page: page.url(), method: resp.request().method(), url: resp.url(), status: resp.status() });
    }
  });

  if (login) {
    try {
      if (!email || !password) {
        throw new Error('Set BAOBAB_TEST_EMAIL and BAOBAB_TEST_PASSWORD, or pass { email, password }, or { login: false }.');
      }
      const resp = await page.request.post(`${apiUrl}/api/v1/authenticate`, {
        headers: { 'Content-Type': 'application/json', Origin: baseUrl },
        data: { email, password },
      });
      if (!resp.ok()) throw new Error(`Login as ${email} failed: HTTP ${resp.status()}`);
      const user = await resp.json();
      await page.goto(baseUrl);
      await page.evaluate((u) => localStorage.setItem('user', JSON.stringify(u)), user);
    } catch (err) {
      // An open browser keeps the Node process alive after the caller's error.
      await browser.close();
      throw err;
    }
  }

  async function settle() {
    // The Vite dev server keeps an HMR websocket open, which networkidle ignores,
    // but slow pages can still exceed the timeout; that is not an error here.
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(500);
  }

  async function goto(urlPath) {
    await page.goto(baseUrl + urlPath);
    await settle();
    return page.url();
  }

  async function shot(name, { fullPage = true } = {}) {
    const file = path.join(shotDir, `${name}.png`);
    await page.screenshot({ path: file, fullPage });
    // The app shell scrolls an inner container, so a full-page shot can stop at
    // the viewport; capture the bottom of that container separately when it overflows.
    if (fullPage) {
      const overflow = await page.evaluate(() => {
        const el = document.querySelector('.flex-1.overflow-y-auto');
        if (!el || el.scrollHeight <= el.clientHeight) return false;
        el.scrollTop = el.scrollHeight;
        return true;
      });
      if (overflow) {
        await page.waitForTimeout(300);
        const bottom = path.join(shotDir, `${name}-bottom.png`);
        await page.screenshot({ path: bottom, fullPage });
        await page.evaluate(() => {
          const el = document.querySelector('.flex-1.overflow-y-auto');
          if (el) el.scrollTop = 0;
        });
        return [file, bottom];
      }
    }
    return [file];
  }

  function report() {
    return { finalUrl: page.url(), consoleErrors: consoleErrors.slice(), failedRequests: failedRequests.slice(), reactWarnings };
  }

  function resetLog() {
    consoleErrors.length = 0;
    failedRequests.length = 0;
    reactWarnings = 0;
  }

  return { browser, context, page, goto, settle, shot, report, resetLog, close: () => browser.close() };
}

module.exports = { openSession };
