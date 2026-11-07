# Organisation settings and white-labelling — Design Doc

2026-11-05 · Drafted by Claude for #1428

## 1. Summary

Site admins (`app_user.is_admin = True`) get an **Organisation settings** page where they can edit their organisation's row in the `organisation` table without a database migration or a deploy. The organisation also gets a **primary colour**, a **secondary colour** and a **favicon**. The webapp applies the colours to its design tokens at start-up and uses the favicon in browser tabs, so each organisation's deployment looks like its own.

**Goals**

- An admin can view and edit the organisation's name, system name, website URL, sender address, privacy policy, languages, logos, PWA icons, currency and Stripe keys from the UI.
- An admin can set a primary colour, a secondary colour and a favicon. Every user on that organisation's domain sees them.
- An admin can upload logos and icons, not only choose from the images bundled into the webapp build.
- Changes reach users on every API instance soon after saving, without a redeploy.

**Non-goals**

- **Editing `domain`.** It is the key `OrganisationResolver` uses to identify the organisation on every request, and it also has to match DNS and `webapp/dispatch.yaml`. Changing it from the UI would lock everyone out. It is shown read-only.
- **Creating organisations, or a super-admin across organisations.** `is_admin` is scoped to the user's own organisation (see Permissions).
- **Full theming** (fonts, surfaces, border radius, dark mode). Only the brand colour tokens change.
- **Per-event branding.** Events keep using the organisation's branding.
- **Rendering the favicon on the server.** The SPA is static, so the browser shows the default favicon until JS runs (see Edge cases).

## 2. Current state

| Layer | Where | Relevant detail |
| --- | --- | --- |
| Model | `api/app/organisation/models.py` | `Organisation`: `name`, `system_name`, `small_logo`, `large_logo`, `icon_logo` (String(100), **bundled filenames**), `domain`, `url`, `email_from`, `system_url`, `privacy_policy`, `languages` (JSON list of `{code, description}`), `iso_currency_code`, three Stripe keys, `pwa_icon_192`/`pwa_icon_512` (String(255), URLs). There are no colour or favicon columns. `PlainOrganisation` is a dataclass copy that the resolver caches. |
| Resolver | `api/app/organisation/resolver.py` | `OrganisationResolver._cache` is a **per-process** dict keyed by `domain`. It is only repopulated on first use, on an unknown domain, or by `bust_cache()`, which only refreshes the process that handles the save. On App Engine with several instances, the other instances keep stale settings until they restart. |
| Request hook | `api/app/__init__.py` `populate_organisation` | Sets `g.organisation` from Origin/Referer for every `/api/*` request, except tasks and `GET /api/v1/file`. |
| API | `api/app/organisation/api.py` | `GET /api/v1/organisation` is public (no auth) and marshals the public fields. `GET/POST /api/v1/stripe-settings` is gated on `is_admin`. Its GET returns the secret keys in plain text, and its POST requires every field. No webapp page uses it. |
| Auth helpers | `api/app/utils/auth.py` | `admin_required` checks `is_admin` in the **token**, not the DB, and doesn't check the organisation. `StripeSettingsApi` reloads the user from the DB but also ignores the organisation. |
| Users | `api/app/users/models.py` | `AppUser.organisation_id` is non-null, and emails are unique per organisation. So an admin belongs to exactly one organisation. |
| File storage | `api/app/files/api.py` | `POST /api/v1/file` (multipart, no auth decorator) stores a blob named by a uuid hex and returns `{file_id}`. `GET /api/v1/file?filename=&disposition=inline` streams it through a temp file, with no auth, no org resolution and no cache headers. |
| Email layout | `api/app/email_template/models.py`, `repository.py` | `EmailLayout.brand_colour` (String(7)) and `logo_url` per organisation/event and language. They fall back to `DEFAULT_BRAND_COLOUR = '#0f5238'`, and `BRAND_COLOUR_RE = ^#[0-9a-fA-F]{6}$` already exists. |
| Bootstrap | `webapp/src/index.js` | Loads the organisation, sets `document.title`, runs `i18nInit(org)`, and injects a blob-URL manifest that uses `pwa_icon_*` and a hardcoded `theme_color: '#0f172a'`. Doesn't touch the favicon or colours. |
| Static head | `webapp/index.html` | Hardcoded Baobab `<link rel="icon">`/`shortcut icon`/`apple-touch-icon` tags under `/favicon/`, and `<meta name="theme-color" content="#0f172a">`. |
| Images | `webapp/src/utils/images.js` | `getImage(filename)` looks the name up in `import.meta.glob('../images/*')`, so logos must be committed to `webapp/src/images/`. It is used in `App.js` (navbar, `icon_logo`), `Home.js` (`large_logo`), `LoginForm.js` and `CreateAccountForm.js` (`small_logo`). |
| Theme tokens | `webapp/src/index.css` `@theme` | Tailwind v4 tokens such as `--color-primary` (#0f5238), `--color-primary-container`, `--color-on-primary-container`, `--color-secondary*`, `--color-action*` (#0132c5, buttons and links) and `--color-ring`. Tailwind v4 utilities read these as CSS variables, so overriding them on `:root` at runtime restyles `bg-primary`, `text-action` and so on. |
| Legacy tokens | `webapp/src/App.css` `:root` | A parallel set, `--clr-primary`, `--clr-action`, `--clr-action-glow` and others, used about 50 times in legacy CSS. There's no Bootstrap dependency: `.navbar`/`.bg-dark` are reimplemented in `App.css` ~L130–210. The top navbar (`.bg-dark`) is already painted with `var(--clr-primary)` and its brand text uses `--clr-on-primary`, but its nav links (`rgba(255, 255, 255, 0.82)`, ~L202) and the language switcher divider (`rgba(255, 255, 255, 0.22)`, ~L254) are hardcoded white. A few brand hex literals are hardcoded outside the tokens: `#0f5238` in `index.html` (loader), `EventStatsComponent.js` (chart), and `EmailLayoutEditor.js`. |
| Admin UI | `webapp/src/pages/home/Home.js` ~L430 | When `user.is_admin`, Home shows "Create New Event" and "Email settings" buttons. That is the only org-admin entry point. Routes are in `webapp/src/App.js` (`/emailSettings` etc. via `PrivateRoute`). |
| Upload UI | `webapp/src/components/FileUpload.js`, `services/file/file.service.js`, `utils/files.js`, `components/Attachments.js` | `fileService.uploadFile(file, onProgress)` returns `{fileId, error}`. `getFileURL(fileId, disposition)` (`utils/files.js:34`) builds the `/api/v1/file?filename=…&disposition=inline` URL. `Attachments.js` ~L88 is an existing image-upload pattern, with resizing. |
| i18n | `webapp/public/locales/{en,fr}/translation.json` | Keys are English sentences (`"Email settings": "Paramètres des courriels"`). Only `en` and `fr` exist. |

## 3. Design

### Data model

Add three nullable columns to `organisation`. `NULL` means "use the Baobab default", so existing organisations look the same after the migration.

```python
# api/app/organisation/models.py
primary_colour = db.Column(db.String(7), nullable=True)    # '#rrggbb'
secondary_colour = db.Column(db.String(7), nullable=True)  # '#rrggbb'
favicon = db.Column(db.String(255), nullable=True)         # image reference, see below
```

Widen `small_logo`, `large_logo` and `icon_logo` from String(100) to String(255) so they can hold an uploaded-image reference, the same size as `pwa_icon_*`. Add all three new fields to `PlainOrganisation`.

**Image references.** Each image field (`small_logo`, `large_logo`, `icon_logo`, `favicon`, `pwa_icon_192`, `pwa_icon_512`) holds one of three kinds of value:

| Value | Example | Resolved by the webapp to |
| --- | --- | --- |
| Bundled filename (has an extension, matches a file in `webapp/src/images/`) | `indaba-logo.png` | the Vite asset URL, as today |
| Absolute URL | `https://…/logo.png` | itself |
| Uploaded file id (32 hex characters) | `3f2a…` | `getFileURL(id, 'inline')` from `utils/files.js` |

This keeps every existing row valid. How uploads are hosted is open question 1.

### API

All new endpoints live in `api/app/organisation/api.py`.

**`GET /api/v1/organisation`** (public, unchanged apart from three new fields): adds `primary_colour`, `secondary_colour` and `favicon`.

**`GET /api/v1/organisation/settings`** (admin): every editable field plus read-only `domain`. Stripe secrets are **never returned**. The response says only whether each one is set.

```json
{
  "id": 1, "domain": "localhost",
  "name": "Deep Learning Indaba", "system_name": "Baobab",
  "url": "https://deeplearningindaba.com", "email_from": "baobab@…", "system_url": "https://baobab.…",
  "privacy_policy": "PrivacyPolicy.md",
  "languages": [{"code": "en", "description": "English"}, {"code": "fr", "description": "Français"}],
  "small_logo": "indaba-logo.png", "large_logo": "…", "icon_logo": "…", "favicon": null,
  "pwa_icon_192": null, "pwa_icon_512": null,
  "primary_colour": "#0f5238", "secondary_colour": null,
  "iso_currency_code": "USD",
  "stripe_api_publishable_key": "pk_live_…",
  "stripe_secret_key_set": true, "stripe_webhook_secret_key_set": true
}
```

**`PUT /api/v1/organisation/settings`** (admin): a partial update in a JSON body. Only the keys present are changed. Sending `null` (or `""`) clears a nullable field. Validation errors return 400 with `{"message": …, "field": …}`, like the email layout API. After saving, the handler calls `OrganisationResolver.bust_cache()` and returns the same body as GET.

| Field | Validation |
| --- | --- |
| `name`, `system_name` | required (non-empty), ≤ 50 chars |
| `url`, `system_url` | required, ≤ 100, `http(s)://` |
| `email_from` | nullable, ≤ 100, contains `@` |
| `privacy_policy` | required, ≤ 100 |
| `languages` | non-empty list of `{code, description}`; `code` unique; `code` in `SUPPORTED_LANGUAGES = ('en', 'fr')` (a new constant in `api/app/organisation/models.py`) |
| image fields | `small_logo`, `large_logo` and `icon_logo` required; the rest nullable; ≤ 255 |
| `primary_colour`, `secondary_colour` | nullable, `BRAND_COLOUR_RE` (reuse it from `app.email_template.repository`) |
| `iso_currency_code` | nullable, 3 uppercase letters |
| `stripe_api_publishable_key` | nullable, ≤ 200 |
| `stripe_api_secret_key`, `stripe_webhook_secret_key` | **write-only**: omitted keeps the stored value, `null` clears it, a string replaces it; ≤ 200 |
| `domain`, `id` | rejected with 400 if present |

`StripeSettingsApi` (`/api/v1/stripe-settings`) is left as is, since this design doesn't need to touch it. Section 4 records that decision and the case for removing it later.

### Cross-instance cache freshness

`bust_cache()` only refreshes the process that handled the PUT. Give `OrganisationResolver` a TTL: store `_loaded_at` when the cache is populated, and repopulate in `resolve_from_domain`/`resolve_from_stripe_signature` when it is older than `ORGANISATION_CACHE_TTL_SECONDS = 60`. That costs one `SELECT * FROM organisation` (a handful of rows) per instance per minute. It also fixes the same latent staleness in the existing Stripe settings.

### Permissions

A new helper, `org_admin_required`, in `api/app/organisation/api.py` (or `app/utils/auth.py`):

1. A valid token is required (401 otherwise).
2. Reload the user from the DB. `is_admin` must be true **and** `user.organisation_id == g.organisation.id`. Otherwise return `FORBIDDEN`.

The DB reload means revoking `is_admin` takes effect immediately instead of when the token expires, two weeks later. The organisation check stops an admin of organisation A from editing organisation B by sending their token to B's domain.

Frontend: the route uses `PrivateRoute`, and the page shows a "You don't have permission" message when `user.is_admin` is false. The API is the real gate.

### Frontend UX

**Entry point.** In `Home.js`, add an "Organisation settings" button (icon `fa-cog`) beside "Email settings" in the `user.is_admin` block.

**Route.** `PrivateRoute exact path="/organisationSettings"` in `App.js` renders `webapp/src/pages/organisationSettings/OrganisationSettings.js`. The path is registered before the `/:eventKey` catch-all.

**Service.** Add `getSettings()` and `updateSettings(partial)` to `webapp/src/services/organisation/organisation.service.js`.

**Page layout.** A single page of `Card` sections and one "Save changes" button. The button sends only the fields that changed. It is disabled while nothing has changed or validation fails. An unsaved-changes guard warns before navigating away.

1. **General**: name, system name, website URL, system URL, sender email, privacy policy, and the domain read-only with a hint saying it can't be changed here.
2. **Branding**
   - Primary colour and secondary colour: a colour input plus a hex text field, the same control as `EmailLayoutEditor.js` (~L190). A "Reset to default" link sets the value to `null`.
   - A live **preview** strip showing a primary button, a secondary button, a link and a header bar in the chosen colours, with a contrast warning (below).
   - Image fields (small logo, large logo, navbar icon, favicon, PWA 192, PWA 512): each shows a thumbnail through `getImage`, plus an "Upload" button using `fileService.uploadFile`, which stores the returned id, and a "Remove" action on nullable fields. The size hints are 32×32 or 48×48 PNG/ICO for the favicon and square PNGs for the PWA icons. Images are limited to `image/*` client-side.
3. **Languages**: a checkbox for each supported language (English, Français), with at least one required. The order follows the list.
4. **Payments**: currency code, publishable key, and the two secret keys as password inputs whose placeholder is "•••• set" or "Not set". Typing replaces the value. A "Clear" action sends `null`.

After a successful save, the page shows a success toast and re-applies branding immediately by calling the same `applyBranding(org)` used at start-up, so the admin sees the result without a reload.

**Applying branding at start-up.** Add `webapp/src/utils/branding.js`, which exports `applyBranding(org)`. `index.js` calls it beside `_injectOrgManifest`.

- **Colours.** For each colour that is set, call `document.documentElement.style.setProperty(...)` on the token set the colour maps to (see open question 2). Derive the shades in JS rather than with CSS `color-mix` so they work in older browsers:
  - `--color-X` and `--clr-X` → the colour
  - `--color-X-container` and `--clr-X-container` → the colour mixed 15% towards white
  - `--color-X-foreground` and `--clr-on-X` → `#ffffff` or `#191c1d`, whichever contrasts more
  - for the action role, also `--color-ring` and `--clr-action-glow` (the colour at 14% alpha)
  When a colour is `null`, the property is removed so the stylesheet default applies.
- **theme-color.** Set `<meta name="theme-color">` and the manifest's `theme_color` to the primary colour, or keep `#0f172a` when it isn't set.
- **Favicon.** When `org.favicon` is set, set `href` on every `link[rel="icon"]` and `link[rel="shortcut icon"]` to the resolved URL and drop their `sizes` and `type` attributes. When `pwa_icon_192` is set, point the `apple-touch-icon` links at it.
- **Images.** Extend `getImage(value)` in `utils/images.js` to resolve all three kinds of reference in the table above. All existing callers keep working.

**Contrast warning.** If the mixing logic produces less than 4.5:1 contrast between the colour and its foreground, the editor shows a non-blocking warning: "Text on this colour may be hard to read."

### Emails

`EmailLayout` resolution falls back to `organisation.primary_colour` before `DEFAULT_BRAND_COLOUR` when no layout sets `brand_colour`. The change goes in `api/app/email_template/repository.py`, where the `DEFAULT_BRAND_COLOUR` default is applied. A layout's explicit colour still wins. `EmailLayoutEditor`'s placeholder shows the inherited colour.

### i18n, accessibility and edge cases

- All new strings go through `t()` with English-sentence keys, and are added to `en` and `fr` `translation.json`.
- Every input has a `<label>`. The colour swatch also has a hex text input, so it can be used from the keyboard. Thumbnails get alt text naming the field.
- **Favicon flash.** Browsers fetch the `index.html` favicon before JS runs, so the Baobab icon shows briefly and some browsers keep a cached favicon until a hard refresh. This is accepted; doing better needs the HTML to be rendered per domain.
- **Image loading cost.** Uploaded images are served through `GET /api/v1/file`, which proxies GCS through a temp file with no cache headers. Without changes, every page load fetches the navbar logo and favicon this way. See open question 1.
- **Bad colour stored.** `applyBranding` ignores any value that doesn't match `^#[0-9a-fA-F]{6}$`, so a bad row can't break the CSS.
- **Removing a language** that users have chosen as their UI language: `i18nInit` already falls back to the first organisation language. Event form translations in the removed language stay in the DB and are simply not offered.

## 4. Decisions

- **`domain` is read-only**: it is the resolver key and must match DNS and `dispatch.yaml`; editing it from the UI breaks every request.
- **Separate `/organisation/settings` endpoint instead of adding auth to `GET /organisation`**: the public endpoint is needed before login, and admin-only fields (Stripe) must not leak into it.
- **Partial PUT with write-only secrets**: an admin can change the colour without re-entering Stripe secrets, and secrets never travel back to the browser.
- **Leave `/api/v1/stripe-settings` alone**: no UI uses it, but removing it is out of scope. It could be deleted in a follow-up now that the settings page covers it.
- **Admin check reloads the user and compares `organisation_id`**: so revocation is immediate and admins can't edit other organisations.
- **60-second resolver cache TTL**: makes edits visible on every App Engine instance within a minute, at the cost of a tiny query.
- **`NULL` colours and favicon mean "Baobab default"**: existing organisations are unchanged and "Reset to default" is simple.
- **Colours applied as runtime CSS-variable overrides in JS**: the Tailwind v4 tokens and the legacy `--clr-*` tokens are already variables, so no build per organisation is needed.
- **Shades derived in JS, not with `color-mix`**: predictable across browsers and testable in one helper.
- **The organisation primary colour becomes the email fallback**: one place to set the brand, while email layouts can still override it.
- **The page lives at `/organisationSettings` and is linked from Home's admin buttons**: this matches how `/emailSettings` is reached today.
- **The top navbar follows the primary colour** (maintainer answer to question 2): `.bg-dark` already reads `--clr-primary`, so it recolours with the other primary tokens. Its hardcoded white link and divider colours are replaced by tokens that `applyBranding` derives from the readable foreground, so text stays legible on a light primary.
- **Hardcoded brand literals are left alone, except the stats chart**: `EventStatsComponent.js` reads `--color-primary` via `getComputedStyle`, so charts follow the brand. The rest are the loader (shown before the organisation loads) or editor placeholders.
- **Languages are limited to locales the webapp ships (`en`, `fr`)**: any other code would give an empty UI.

## 5. Open questions

Answered by the maintainer on #1431:

1. **A**: reuse `POST/GET /api/v1/file` and add the cache header for inline images (Task 5 is in scope).
2. **A**, and the top header/navbar also uses the primary colour (see Decisions and Task 6).
3. **A**: the Payments section is included, with write-only secrets.

The original options are kept below for reference.

1. **How should uploaded images be hosted?** Logos and favicons are loaded on every page view by every user.
   - A: Reuse `POST /api/v1/file` and store the file id. Serve it through `GET /api/v1/file`, adding a `Cache-Control: public, max-age=86400` header for inline images. No new infrastructure, but every first view still proxies through the API, and the file id is guessable only if leaked (ids are uuid4).
   - B: Add an admin-only `POST /api/v1/organisation/settings/image` that uploads to a **public** GCS bucket or prefix and stores the absolute public URL. Images are served straight from GCS or the CDN, which is fastest, but needs a public bucket created and configured per environment (`GCP_PUBLIC_BUCKET_NAME`) and an emulator equivalent locally.
   - C: No uploads. Admins pick a bundled filename or paste an absolute URL hosted elsewhere. This is the simplest, but doesn't really deliver self-service white-labelling.
   - Recommendation: **A**. It works in every environment today, and the cache header removes most of the repeat cost. B can replace it later without changing the stored format, because absolute URLs are already supported.

2. **Which UI tokens should "primary" and "secondary" drive?** The design system has three brand roles: *primary* (green: headers, badges, progress bars), *secondary* (a muted second green, little used), and *action* (electric blue: buttons, links, focus rings).
   - A: Primary → `primary` tokens, secondary → `action` tokens. The two colours the admin picks are the two users notice most. The existing `secondary` green is derived from primary.
   - B: Primary → `primary`, secondary → `secondary`, action stays Baobab blue. This matches the names literally, but the secondary colour would barely show and the buttons would stay blue for every organisation.
   - C: Expose three colours (primary, secondary, action).
   - Recommendation: **A**, labelled in the UI as "Primary colour (headers and highlights)" and "Accent colour (buttons and links)", so admins know what each one changes.

3. **Should the page include Stripe/payment settings?** They are columns on the `organisation` table and no UI exists for them today, but they are secrets that move real money.
   - A: Include them, write-only, as designed above.
   - B: Leave payments out of this page and keep them DB-only (or put them on a separate page later).
   - Recommendation: **A**. Write-only secrets and the stricter admin check make it safe, and it removes the last reason to edit `organisation` by hand. If maintainers want an extra safeguard, the Payments section could require re-entering the password; that is not designed here.

## 6. Implementation plan

### Task 1: Organisation columns and migration

- **Depends on:** none
- **Files:** `api/app/organisation/models.py`, `api/migrations/versions/<rev>_add_organisation_branding.py`, `api/app/organisation/api.py`, `api/app/organisation/tests.py`
- **Change:** Add nullable `primary_colour` String(7), `secondary_colour` String(7) and `favicon` String(255) to `Organisation` and `PlainOrganisation`. Widen `small_logo`, `large_logo` and `icon_logo` to String(255) (`op.alter_column`). Add `SUPPORTED_LANGUAGES = ('en', 'fr')`. Add the three new fields to `OrganisationApi.organisation_fields`. The migration's `down_revision` must be the current head (`flask db heads`), with the revision and file name in the style of `724757fece76_add_organisation_pwa_icons.py`.
- **Acceptance criteria:**
  - `GET /api/v1/organisation` returns `primary_colour`, `secondary_colour` and `favicon` (null for existing rows).
  - `flask db upgrade` then `flask db downgrade -1` then `flask db upgrade` succeeds against the dev DB.
- **Tests:** extend `test_organisation_from_origin` to assert the three keys are present and null, plus one test with values set on the org.

### Task 2: Resolver cache TTL

- **Depends on:** none
- **Files:** `api/app/organisation/resolver.py`, `api/app/organisation/tests.py`
- **Change:** Record `_loaded_at` (from `time.monotonic()`) in `_populate_cache`. Repopulate in `resolve_from_domain` and `resolve_from_stripe_signature` when the cache is older than `ORGANISATION_CACHE_TTL_SECONDS = 60` (a module constant). `reset_cache()` also clears `_loaded_at`.
- **Acceptance criteria:**
  - Within the TTL, a DB change isn't visible. After the TTL, the next resolve returns the new value.
- **Tests:** change an org's `name` in the DB directly (no `bust_cache`), resolve, and assert the old name. Then patch `time.monotonic` past the TTL, resolve, and assert the new name.

### Task 3: Organisation settings API

- **Depends on:** Task 1
- **Files:** `api/app/organisation/api.py`, `api/app/routes.py`, `api/app/organisation/tests.py`
- **Change:** Add `OrganisationSettingsApi` with GET and PUT at `/api/v1/organisation/settings`, and the `org_admin_required` check (token required; DB user `is_admin` and `organisation_id == g.organisation.id`). The GET response shape, the PUT partial-update semantics and the validation table are in section 3 under "API". Reuse `BRAND_COLOUR_RE` from `app.email_template.repository`. Call `OrganisationResolver.bust_cache()` after saving.
- **Acceptance criteria:**
  - GET never includes `stripe_api_secret_key` or `stripe_webhook_secret_key` values, only `*_set` booleans.
  - PUT with `{"primary_colour": "#123456"}` changes only that column. The following `GET /api/v1/organisation` returns it.
  - PUT omitting the Stripe secrets keeps them. `null` clears them.
  - PUT with `domain`, a bad colour, an empty `name`, an unsupported language code, duplicate language codes or an empty language list returns 400 with the `field` named.
  - A non-admin gets 403. An admin of a different organisation calling with this org's Origin gets 403. No token gets 401.
- **Tests:** one test per acceptance criterion. Use two organisations (`add_organisation` twice, with different domains) for the cross-org test. Capture user and org ids in `setUp` (see "Avoiding DetachedInstanceError" in `.claude/CLAUDE.md`).

### Task 4: Email layout falls back to organisation colour

- **Depends on:** Task 1
- **Files:** `api/app/email_template/repository.py` (where `DEFAULT_BRAND_COLOUR` is applied when resolving a layout), `api/app/email_template/tests/…` (match the existing test layout)
- **Change:** When no event or organisation layout sets `brand_colour`, use `organisation.primary_colour` if set, then `DEFAULT_BRAND_COLOUR`.
- **Acceptance criteria:**
  - A rendered email for an org with `primary_colour='#123456'` and no layout colour uses `#123456` for buttons. A layout colour still overrides it. With neither set, the result is unchanged.
- **Tests:** those three cases at the repository/service level.

### Task 5: Uploaded image serving

- **Depends on:** none
- **Files:** `api/app/files/api.py`, `api/app/files/tests.py`
- **Change:** In `FileUploadAPI.get`, when the resolved disposition is `inline` and the content type starts with `image/`, set `Cache-Control: public, max-age=86400` on the response.
- **Acceptance criteria:** an inline image response has the header, and an attachment download doesn't.
- **Tests:** both cases, using the dummy storage client the existing file tests use.

### Task 6: Frontend branding helper and start-up wiring

- **Depends on:** Task 1
- **Files:** `webapp/src/utils/branding.js` (new), `webapp/src/utils/images.js`, `webapp/src/index.js`, `webapp/src/pages/eventStats/components/EventStatsComponent.js`, `webapp/src/App.css`
- **Change:**
  - `getImage(value)` resolves a bundled filename, an absolute URL or an uploaded file id (`/^[0-9a-f]{32}$/` → `getFileURL(id, 'inline')` from `utils/files.js`). It returns `undefined` for empty values.
  - `branding.js` exports `applyBranding(org)`, which:
    - sets or removes the colour CSS variables for the primary role (`--color-primary`, `--color-primary-container`, `--color-primary-foreground`, `--clr-primary`, `--clr-primary-container`, `--clr-on-primary`) and for the secondary role (per the answer to open question 2; by default the action role, `--color-action`, `--color-action-container`, `--color-action-foreground`, `--color-ring`, `--clr-action`, `--clr-action-container`, `--clr-on-action`, `--clr-action-glow`);
    - also sets `--clr-on-primary-muted` (the primary foreground at 82% alpha) and `--clr-on-primary-divider` (the foreground at 22% alpha), and removes them when primary is null;
    - updates `meta[name=theme-color]`;
    - repoints the favicon and apple-touch-icon links.
    It also exports `contrastRatio(hexA, hexB)` and `readableForeground(hex)` for the editor. It ignores invalid hex values.
  - `index.js` calls `applyBranding(org)` after `i18nInit`, and `_injectOrgManifest` uses `org.primary_colour || '#0f172a'` for `theme_color`. `_injectOrgManifest` runs its `pwa_icon_*` values through `getImage` so uploaded ids work there too.
  - `EventStatsComponent.js` replaces its hardcoded `'#0f5238'` chart colour with the computed `--color-primary`.
  - In `webapp/src/App.css`, define `--clr-on-primary-muted: rgba(255, 255, 255, 0.82)` and `--clr-on-primary-divider: rgba(255, 255, 255, 0.22)` in `:root`, and use them for the navbar nav links (~L202) and the language switcher divider (~L254) instead of the literals, so the navbar text follows the primary colour's foreground.
- **Acceptance criteria:**
  - `pnpm run build` passes.
  - With `primary_colour` and `secondary_colour` set in the dev DB, `/` shows the new colours on primary and action elements, the top navbar is the primary colour with readable text, and the tab shows the configured favicon.
  - With all three null, the app looks exactly as before.
- **Verification:** scenarios 4 and 5.

### Task 7: Organisation settings page

- **Depends on:** Tasks 3, 5 and 6
- **Files:** `webapp/src/pages/organisationSettings/OrganisationSettings.js` (new, plus small subcomponents in `components/` as needed), `webapp/src/services/organisation/organisation.service.js`, `webapp/src/App.js`, `webapp/src/pages/home/Home.js`, `webapp/public/locales/{en,fr}/translation.json`
- **Change:**
  - Add `getSettings` and `updateSettings` to the service.
  - Register `PrivateRoute exact path="/organisationSettings"` before `/:eventKey`.
  - Add the "Organisation settings" button in Home's `user.is_admin` block.
  - Build the page as described in section 3 under "Frontend UX": the General, Branding (with live preview and contrast warning), Languages and Payments sections; save sends only the changed keys; server `field` errors show next to the input; `applyBranding` runs after save; the unsaved-changes guard; the "no permission" state when `!user.is_admin`. The colour controls copy the pattern in `EmailLayoutEditor.js`, and uploads use `fileService.uploadFile`.
- **Acceptance criteria:**
  - All strings are translated in `en` and `fr`.
  - `pnpm run build` passes.
  - Saving a colour recolours the page without a reload.
  - Secret inputs never show the stored value.
- **Verification:** scenarios 1–3 and 6–8.

## 7. Verification scenarios

These use the seeded `agent-test` environment (`flask seed-agent`). The organisation served at `localhost` is the one being edited. Reset any changed settings afterwards (set the colours and favicon back to null and restore the original names).

| # | Role | Start at | Steps | Expected |
| --- | --- | --- | --- | --- |
| 1 | admin | `/` | Click "Organisation settings" | The page loads with the current values. The domain is read-only. The Stripe secret fields show "set"/"Not set", never the value. |
| 2 | admin | `/organisationSettings` | Change the system name, save, reload | A success message appears. After the reload, the navbar and the browser tab title show the new system name. |
| 3 | admin | `/organisationSettings` | Set primary `#7b1fa2` and accent `#e65100`, check the preview, save | The preview updates as the values are typed. After saving, the page's buttons and links are orange, and the top navbar and primary elements purple, without a reload. |
| 4 | user | `/` (new session, after scenario 3) | Log in as the plain user and browse Home and an event page | The same colours show on every page, including the navbar. Text on coloured buttons and in the navbar is readable. |
| 5 | admin | `/organisationSettings` | Upload a PNG as the favicon and another as the navbar icon, save, reload | The tab shows the uploaded favicon (after JS runs) and the navbar shows the new icon. |
| 6 | admin | `/organisationSettings` | Enter `#12345` as the primary colour; clear the name; untick every language | Save is disabled or the field errors show; nothing is saved. |
| 7 | admin | `/organisationSettings` | Click "Reset to default" on both colours and remove the favicon, save, reload | The Baobab green and blue return and the default favicon shows. |
| 8 | user (not admin) | `/organisationSettings` | Open the URL directly | A "no permission" message shows, there's no form, and `GET /api/v1/organisation/settings` returns 403. Home shows no "Organisation settings" button. |
| 9 | event-admin | `/` | Look at Home's admin buttons | No "Organisation settings" button (event admins aren't org admins). |

Partly checkable in a seeded environment: in scenario 5, browsers cache favicons aggressively, so check the `<link rel="icon">` `href` in the DOM as well as the tab. Scenario 4 also covers the email fallback (Task 4) only through backend tests, because emails aren't delivered locally. The Payments section can be saved with dummy keys, but a real Stripe payment isn't exercised.

## 8. Migration and rollout

- One migration adds three nullable columns and widens three columns from String(100) to String(255). No backfill is needed. `NULL` keeps the current look for every organisation.
- No ordering constraints. The new frontend tolerates the API not yet returning the new fields (they read as `undefined`, which means defaults), and the old frontend ignores them.
- After deploy, other API instances pick up settings changes within 60 seconds because of the resolver TTL.
