# <Feature name> — Design Doc

<YYYY-MM-DD> · Drafted by Claude for #<issue>

## 1. Summary

<Two or three sentences: what users will be able to do, and for whom.>

**Goals**

- <outcome>

**Non-goals**

- <thing a reader might expect that this deliberately leaves out, and why>

## 2. Current state

<What exists today that this builds on or changes. Use a table to map it.>

| Layer | Where | Relevant detail |
| --- | --- | --- |
| Models | `api/app/...` | |
| API | `api/app/.../api.py` | |
| Frontend | `webapp/src/pages/...` | |
| Service | `webapp/src/services/...` | |

## 3. Design

<Sections as needed, e.g. Data model, API, Permissions, Frontend UX, Emails, i18n. Show model and API shapes in code blocks. Name files, components and endpoints.>

### Data model

### API

### Permissions

### Frontend UX

### i18n, accessibility and edge cases

## 4. Decisions

<Choices made that a reviewer could reverse. One line each with the reason.>

- **<decision>**: <reason>

## 5. Open questions

<Only questions whose answer changes the design substantially. Options plus a recommendation.>

1. **<question>**
   - A: <option> — <tradeoff>
   - B: <option> — <tradeoff>
   - Recommendation: <A or B, and why>

## 6. Implementation plan

<Ordered tasks. Each must stand on its own for an implementer who has read only this section, `.claude/CLAUDE.md` and the files listed.>

### Task 1: <title>

- **Depends on:** none
- **Files:** `api/app/...`
- **Change:** <what to build>
- **Acceptance criteria:**
  - <checkable statement>
- **Tests:** <pytest cases to add: positive, negative, permission>

### Task 2: <title>

- **Depends on:** Task 1
- **Files:** `webapp/src/...`, `webapp/public/locales/{en,fr}/translation.json`
- **Change:**
- **Acceptance criteria:**
- **Verification:** scenario <n> below

## 7. Verification scenarios

<End-to-end flows to drive in the browser once implemented.>

| # | Role | Start at | Steps | Expected |
| --- | --- | --- | --- | --- |
| 1 | Event admin | `/<event>/...` | | |
| 2 | Applicant without permission | | | Access denied / item hidden |

## 8. Migration and rollout

<Schema migrations, data backfills, settings defaults for existing events, anything that must happen in order on deploy. "None" if none.>
