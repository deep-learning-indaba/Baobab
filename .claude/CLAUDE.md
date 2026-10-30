# Baobab Project

## Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## Code Comments

Write comments that explain the code as it stands, not the history of how it got there.

- No narrative framing: never write "used to", "previously", "this used to break X", "now fixes", "the bug was", "no longer does X because it used to Y". A comment is not a changelog entry — the reader has no reason to care what the code looked like before your edit.
- If a comment is documenting *why this exists as a guard*, say so as a present-tense or hypothetical fact about the code, not a past-tense story about a defect: prefer "Without this, X would happen" over "This used to cause X, which is why...". Prefer "Omitting a key here falls back to the stored value, so it can never be cleared" over "Previously omitting a key meant it could never be cleared".
- Only comment when the WHY is genuinely non-obvious: a hidden constraint, an invariant the code depends on, a workaround for a specific external limitation, or behavior that would surprise a reader. If removing the comment wouldn't confuse a future reader, don't add it.
- Never reference the current task, PR, or fix ("fixes issue where...", "added for the X flow") — that belongs in the commit message or PR description, not the code, and it rots as the codebase evolves.
- This applies to docstrings and multi-line comment blocks too, not just inline `//`/`#` comments.

## Frontend Verification

After making substantial frontend changes, or building new pages, use `/screenshot <path>` to take a screenshot and review it. The skill handles Playwright setup, auth, and has a critical review checklist to catch clipping, margin issues, and layout bugs. Do not use this for minor changes like changing alignment, unless the user has asked more than once for the same change.

There is no frontend unit-test suite. Verify frontend changes with `pnpm run build` in `webapp/` (catches import and syntax errors), then by driving the app: `/screenshot` for a single page, the `verify-feature` skill for multi-step flows.

## Automated workflow

Skills for working from GitHub issues: `fix-bug`, `design-feature`, `implement-feature`, `verify-feature`, in `.claude/skills/`. Subagents are in `.claude/agents/`. The shared rules (labels, branches, budgets, headless behaviour, safety) are in `.claude/agent-workflow.md`.

## Line endings

Some backend files are committed with CRLF line endings (e.g. `api/app/reviews/api.py`, `api/app/events/mixins.py`). Text-mode scripted edits (Python `open().read()`/`write()`, some `sed` invocations) convert them to LF and turn a small change into a whole-file diff. Use the Edit tool or binary-mode scripts, and after scripted edits check `git diff --numstat` for files whose added/removed counts are close to their full length.

## Translations
The application supports i18n. Whenever you add new text to the front-end, make sure it is wrapped in "t" from react-i18next, and ensure that you add the translations to the translation.json files in webapp/public/locales for en and fr.

## Backend
Write tests for any new backend functionality and run them with docker-compose.

### Running backend tests

Run pytest inside the already-running `web` container. `docker-compose run` starts a fresh container, which has been seen taking ~25 minutes to start while the tests themselves take seconds.

```bash
# All tests
docker-compose exec -T web sh -c "cd /code/api && python -m pytest -q -p no:warnings"

# Specific module / file / class / test (use :: separators)
docker-compose exec -T web sh -c "cd /code/api && python -m pytest app/forms -q -p no:warnings"
docker-compose exec -T web sh -c "cd /code/api && python -m pytest app/announcements/tests.py::AnnouncementApiTest::test_name -v"
```

pytest must run from the `api` subdirectory, not the repo root. If the `web` container isn't up, fall back to `docker-compose run --rm -w /code/api web pytest ...`.

The full suite (~1,340 tests) takes about 17 minutes in the container, and `pytest-xdist` isn't installed there, so `-n auto` fails. Run the modules you touched while iterating. For a full run, start it detached and poll its log, so a quiet `| tail` doesn't look like a hang:

```bash
docker-compose exec -T -d web sh -c "cd /code/api && python -m pytest -v -p no:warnings > /tmp/pt.log 2>&1; echo EXIT=\$? >> /tmp/pt.log"
docker-compose exec -T web sh -c "grep -c PASSED /tmp/pt.log; grep -E 'FAILED|ERROR|EXIT=' /tmp/pt.log"
```

Tests use in-memory SQLite (`app/utils/testing.py`), so they never touch the dev Postgres data. SQLite also differs from production Postgres for some SQL: for date grouping, use `app/utils/timeseries.daily_counts` rather than `CAST(x AS DATE)`.

### Direct DB access (dev)

```bash
docker-compose exec -T db psql -U docker -d docker
```

Both the role and database are named `docker` (not `baobab` or `postgres`). Table names are singular snake_case (`event`, `app_user`, `invited_guest`, ...), not plural — check with `\dt` if unsure. Useful for temporarily seeding/tweaking rows (e.g. shifting an event's `start_date`) to exercise conditional logic that's hard to trigger with existing fixtures; revert the change afterward since this is shared dev data.

### Database migrations

Migrations are managed through **Flask-Migrate** (`migrate = Migrate(app, db)` in `app/__init__.py`), not the raw `alembic` CLI. Running bare `alembic` commands (even with `-c migrations/alembic.ini`) fails with `No 'script_location' key found` — that config is supplied programmatically by Flask-Migrate at runtime, not present in `alembic.ini` itself. Always go through `flask db ...`:

```bash
# Find the current head revision (needed for a new migration's down_revision)
docker-compose run --rm -w /code/api web flask db heads

# Apply migrations to the dev DB
docker-compose run --rm -w /code/api web flask db upgrade
```

Migration files live in `api/migrations/versions/`, named `<revision>_<slug>.py`, with `revision`/`down_revision` as short random hex strings (not sequential numbers) — copy the format from an existing file rather than hand-inventing one, and set `down_revision` to whatever `flask db heads` reports so you don't fork history.

Note `pytest` does **not** run migrations — `app/utils/testing.py` builds the schema straight from the models via `db.create_all()`/`drop_all()`. A green test suite says nothing about whether the migration file itself is valid; verify it separately with `flask db upgrade` against the docker dev DB.

### Avoiding `DetachedInstanceError` in API tests

Any test that issues a request through the Flask test client (`self.app.get/post/put/delete(...)`) tears down `db.session` when that request completes. Every ORM object loaded through the *old* session — typically `self.user`/`self.event`/anything created in `setUp()` before the first request — becomes detached, and SQLAlchemy's default `expire_on_commit=True` means even re-reading `.id` on it after that point needs a fresh SELECT the dead session can't run, raising `DetachedInstanceError`. This has bitten every new API test file so far (`api/app/documents/tests/test_api.py`, `test_authorization.py`) and will bite the next one too if not designed around up front:

- **Capture plain ids immediately after creation**, before any request is made — `self.user_id = self.user.id` in `setUp()`, not `self.user.id` used later inline in a test body. This is the existing convention in `app/forms/tests/test_authorization.py`; keep using it in new test files rather than reaching for `self.user.id` past the test's first HTTP call.
- Within a single test method, if an object is created *between* two requests (e.g. `variant = self.make_variant(...)` then `self.put_json(...)` then `self.app.delete(...)` using `variant.id` again), capture its `.id` into a local variable right after creation — the second request will have already detached it by the time you read it again.
- For shared test-factory helpers that take a model instance as an argument (rather than a bare id) and might be called with an already-detached object, read the primary key via `sqlalchemy.inspect(obj).identity[0]` instead of `obj.id` — identity is cached on the instance state independently of session attachment, so it never raises even when the object is fully detached. See `_pk()` in `app/documents/tests/base.py` for the pattern.

## Architecture Notes

- Frontend: React (Vite dev server on port 8080)
- Backend: Python/Flask API on port 5000
- Both run via Docker Compose — see `docker-compose.yml`
- Shared form editor components: `webapp/src/pages/createApplicationForm/components/` — used by both the application form (`/applicationform`) and review form (`/reviewForm`) editors
- Form editor CSS: `webapp/src/pages/createApplicationForm/Form.css` — all rules scoped under `.application-form-wrap` to avoid bleeding from other pages


