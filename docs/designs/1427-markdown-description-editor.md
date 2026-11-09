# Markdown editor for form description fields — Design Doc

2026-11-08 · Drafted by Claude for #1427

## 1. Summary

In the new form editor (`/:eventKey/forms/new` and `/:eventKey/forms/:formId/edit`), the section and question **description** fields become a small GitHub-style markdown editor: a **Write / Preview** tab pair and a toolbar of formatting buttons above a plain textarea. Event admins building application or review forms can then see how a description will look to applicants before they save, and add common formatting without remembering the syntax.

**Goals**

- Each description textarea for sections and questions (and the form description, see Decisions) has a Write tab and a Preview tab. Preview renders the text with the same `MarkdownRenderer` the form renderer uses, so what the admin sees matches what applicants see.
- A toolbar inserts heading, bold, italic, link, bulleted list, numbered list and quote syntax around the current selection, and keeps the browser's undo history working.
- It works in every language column of `TranslatableFieldGroup`, and auto-translate, re-translate, disabled-while-translating and the existing validation behave as they do today.

**Non-goals**

- **Legacy editors** (`/applicationform`, `/reviewForm`, `webapp/src/pages/createApplicationForm/`). The issue excludes them.
- **Other markdown fields** that also use `TranslatableFieldGroup` (announcement body in `AnnouncementsAdmin.js`, programme session descriptions in `ProgrammeEditor.js`, document fields). The new component is opt-in through a prop, so they can adopt it later in one line each, but changing those pages isn't part of this issue.
- **Headlines, placeholders and option labels.** `QuestionRenderer` renders the headline as plain text inside an `<h3>`, and placeholders and option labels are not rendered as markdown, so a markdown editor there would be misleading.
- **Syntax highlighting, image upload, @mentions, tables or math buttons.** The renderer supports GFM tables and KaTeX math (`remark-gfm`, `remark-math`), so admins can still type them and see them in Preview; they just don't get a toolbar button.
- **Backend changes.** Descriptions are already stored as free text in `form_section_translation.description` and `form_question_translation.description`; nothing about storage or the API changes.

## 2. Current state

| Layer | Where | Relevant detail |
| --- | --- | --- |
| Editor page | `webapp/src/pages/eventHome/EventHome.js` ~L795–825 | Routes `forms/new` and `forms/:formId/edit` render `FormEditorPage`, which renders `FormEditor` (`webapp/src/pages/formEditor/FormEditor.js`). Used for application, review and generic forms (`includeReviewTypes` for review forms). |
| Form description | `FormEditor.js` ~L281–290 | `TranslatableFieldGroup` with `label={t('Form Description')}`, `multiline={true}`. Rendered as markdown in `FormRenderer.js` ~L562 (`<MarkdownRenderer source={formDescription} />`). |
| Section description | `formEditor/components/SectionCard.js` ~L141–149 | `TranslatableFieldGroup` with `label={t('Section Description')}`, `fieldName="description"`, `multiline={true}`. |
| Question description | `formEditor/components/QuestionCard.js` ~L206–214 | `TranslatableFieldGroup` with `label={t('Description')}`, `multiline={true}`. Shown for every question type, including `information` / `sub-heading`, where the description is the whole content. |
| Field group | `formEditor/components/TranslatableFieldGroup.js` | One column per event language (`flex gap-4 flex-wrap`, each `flex-1 min-w-[200px]`). For `multiline` it renders a `<textarea rows={3} className="... resize-y min-h-[80px]">`. Handles auto-translate from the primary language after 1 s of idle typing, a Re-translate button per non-primary column, disabling only the target columns while a translation is in flight, and the "Required in all languages" error. Also used by `AnnouncementsAdmin`, `ProgrammeEditor`, `OptionsEditor` and several document pages. |
| Renderer | `webapp/src/components/MarkdownRenderer.js` | `react-markdown` v8 with `remark-math`, `remark-gfm`, `remark-breaks`, `rehype-katex`; links open in a new tab. Raw HTML is not rendered (react-markdown default). Output is wrapped in `.markdown-container`, styled in `webapp/src/App.css` section 21 (headings, lists, blockquotes, code) because Tailwind preflight strips them. |
| Respondent view | `formRenderer/components/SectionRenderer.js` ~L42–46, `QuestionRenderer.js` ~L196–202 | Section: `<div className="text-muted-foreground text-base leading-relaxed w-full mb-8"><MarkdownRenderer …/></div>`. Information/sub-heading: `<div className="text-muted-foreground leading-relaxed">`. Single-checkbox uses the description as its label via `FormCheckbox`. |
| Existing toolbar | `webapp/src/pages/emailTemplates/EmailTemplateEditor.js` L17–30, ~L339–347 | A local `ToolbarButton` (icon + label) driving `LiquidEditor`'s `wrap(before, after, placeholder)` for Bold / Italic / Heading / List / Link. `LiquidEditor` is CodeMirror 6 with Liquid autocompletion, tied to the email schema. |
| Existing preview | `webapp/src/pages/eventApp/AnnouncementsAdmin.js` ~L330–347 | An ad-hoc always-visible "Preview" box under the body field, primary language only. |
| Tabs | `EmailTemplateEditor.js` ~L270–285, ~L369–380 | `role="tablist"` / `role="tab"` buttons with `aria-selected`, `bg-primary text-white` for the active tab. |
| i18n | `webapp/public/locales/{en,fr}/translation.json` | Already has `Bold`, `Italic`, `Heading`, `Link`, `List`, `Preview`, `bold text`, `link text`. Missing: `Write`, `Nothing to preview`, `Numbered list`, `Quote`, `italic text`, `list item`, `quote`, `Formatting`. |

## 3. Design

### Component: `MarkdownEditor`

New file `webapp/src/components/MarkdownEditor.js`, next to `MarkdownRenderer`, so pages outside the form editor can adopt it.

```jsx
<MarkdownEditor
  value={value}
  onChange={(next) => ...}        // receives the new string, like the textarea onChange today
  onBlur={...}
  placeholder={placeholder}
  disabled={disabled}
  hasError={hasError}              // red border, same classes as inputCls(true)
  ariaLabel={`${label} (${code})`} // textarea and tablist labels
  previewClassName="text-muted-foreground leading-relaxed"
  rows={3}
/>
```

Layout, top to bottom, inside one bordered box (border colour follows `hasError`, focus ring on `:focus-within`):

```
┌────────────────────────────────────────────────────────────┐
│ [Write] [Preview]                    H  B  I  🔗  •  1.  ❝ │  ← header row, bg-surface-low
├────────────────────────────────────────────────────────────┤
│ textarea (Write)  /  rendered markdown (Preview)           │
└────────────────────────────────────────────────────────────┘
```

- **Tabs**: two `role="tab"` buttons in a `role="tablist"`, styled as small pills like the email editor's tabs. State `mode: 'write' | 'preview'` is local to each editor instance; it starts on Write.
- **Preview**: `<div className={previewClassName}><MarkdownRenderer source={value} /></div>`, in a box with the same min-height as the textarea so switching tabs doesn't make the page jump. An empty value shows `t('Nothing to preview')` in muted italic.
- **Toolbar**: icon-only buttons (Font Awesome, already loaded) with `title` and `aria-label` set to the translated name. Hidden in Preview mode, as on GitHub. When the header row is too narrow (columns are `min-w-[200px]`), the toolbar wraps onto a second line under the tabs (`flex-wrap`).
- **Textarea**: keeps today's classes, `resize-y`, `min-h-[80px]`, `rows`, and passes `disabled`, `placeholder` and `onBlur` through.
- **Disabled**: when `disabled` is true (the column is being auto-translated), the toolbar buttons are disabled too; the tabs stay usable so Preview still works.

### Toolbar actions

A pure helper, `webapp/src/components/markdownFormatting.js`, computes each edit so it's easy to reason about and reuse:

```js
// Returns { text, selectionStart, selectionEnd } for the replacement of
// value.slice(start, end), plus where the selection should land afterwards.
applyFormat(action, value, start, end, placeholderText)
```

| Button | Icon | Action | Inline / line | No selection inserts |
| --- | --- | --- | --- | --- |
| Heading | `fa-heading` | prefix `### ` | line prefix | `### Heading` |
| Bold | `fa-bold` | wrap `**…**` | inline | `**bold text**` |
| Italic | `fa-italic` | wrap `_…_` | inline | `_italic text_` |
| Link | `fa-link` | `[sel](https://)`, cursor selects `https://` | inline | `[link text](https://)` |
| Bulleted list | `fa-list-ul` | prefix `- ` | line prefix, every selected line | `- list item` |
| Numbered list | `fa-list-ol` | prefix `1. `, `2. `, … | line prefix, every selected line | `1. list item` |
| Quote | `fa-quote-right` | prefix `> ` | line prefix, every selected line | `> quote` |

Rules:

- **Inline** actions wrap the selection. With no selection they insert the placeholder text and select it, so typing replaces it.
- **Line-prefix** actions expand the selection to whole lines and prefix each one. If the selection starts mid-line, the change applies to that whole line. If the cursor is on a non-empty line with nothing selected, the line is prefixed.
- **Toggle off**: if every affected line already has the prefix, or the selection is already wrapped in the same markers, the action removes them. This matches GitHub and stops repeated clicks from stacking `****`.
- Block prefixes need a blank line before them to render as a block after a paragraph; the helper inserts a leading `\n` when the previous line is non-empty and isn't itself a list/quote line.

Applying an edit (`MarkdownEditor`):

1. Read `selectionStart`/`selectionEnd` from the textarea ref and call `applyFormat`.
2. Focus the textarea, select the range being replaced, and call `document.execCommand('insertText', false, text)`. This goes through the browser's editing pipeline, so Ctrl+Z undoes the formatting and React's `onChange` fires with the new value, which means auto-translate's debounce and `manuallyEdited` tracking in `TranslatableFieldGroup` work unchanged.
3. If `execCommand` returns false (it's deprecated, though every current browser supports `insertText` in textareas), fall back to building the new string and calling `onChange(newValue)` directly; undo won't cover that edit.
4. Set the selection from the helper's result on the next frame (`requestAnimationFrame`), after React re-renders the controlled value.

Keyboard shortcuts in the textarea: Ctrl/⌘+B (bold), Ctrl/⌘+I (italic), Ctrl/⌘+K (link). Nothing else is intercepted.

### Wiring into `TranslatableFieldGroup`

Add a `markdown` prop (default `false`). When `markdown && multiline`, render `MarkdownEditor` in place of the `<textarea>`, passing the same `value`, `onChange` (unwrapped to `(v) => handleChange(language.code, v)`), `onBlur`, `placeholder`, `disabled={disabled || isTranslatingThisField}`, `hasError`, plus `previewClassName`. Everything else in the group (language badge, error text, Re-translate button, translating spinner) stays as is.

Add a `previewClassName` prop to `TranslatableFieldGroup` and pass it through, so each caller can match its respondent-side wrapper:

| Caller | Field | `previewClassName` |
| --- | --- | --- |
| `FormEditor.js` | Form Description | `text-muted-foreground leading-relaxed` |
| `SectionCard.js` | Section Description | `text-muted-foreground text-base leading-relaxed` |
| `QuestionCard.js` | Description | `text-muted-foreground leading-relaxed` |

Other `TranslatableFieldGroup` callers don't pass `markdown`, so they're unchanged.

A short hint sits under the label of markdown groups: `t('Markdown is supported.')`, in `text-xs text-muted-foreground`, so admins know typing the syntax directly also works.

### Permissions

No change. The editor pages are already restricted to event admins; this is a presentational change on the client.

### i18n, accessibility and edge cases

- New keys (en and fr): `Write`, `Nothing to preview`, `Numbered list`, `Bulleted list`, `Quote`, `italic text`, `list item`, `quote`, `Markdown is supported.`, `Formatting`. Existing keys reused: `Preview`, `Bold`, `Italic`, `Heading`, `Link`, `bold text`, `link text`. Placeholder text inserted by the toolbar is in the **UI** language, not the column's language; admins replace it immediately, so this is acceptable.
- Tabs use `role="tablist"`/`role="tab"`/`aria-selected`, and the panel has `role="tabpanel"`. The toolbar is `role="toolbar"` with `aria-label={t('Formatting')}`. Buttons are `type="button"` so they never submit anything.
- Switching to Preview in one language column doesn't affect the others; each column has its own tab state.
- If auto-translate fills a column while it is showing Preview, the preview simply re-renders with the new value.
- `remark-breaks` is on, so a single newline renders as a line break in Preview, the same as for respondents.
- Raw HTML in a description is shown as text in both Preview and the live form (react-markdown's default), so Preview stays faithful.
- `SectionCard`/`QuestionCard` unmount their bodies when collapsed, so tab state resets to Write on re-expand. That's fine.

## 4. Decisions

- **Plain `<textarea>` with a toolbar, not CodeMirror** (see open question 1): keeps the existing disabled, placeholder, blur and resize behaviour, needs no new dependency, and the description fields are short.
- **Shared component in `webapp/src/components/`**, opt-in via `markdown` on `TranslatableFieldGroup`: announcements and programme can adopt it later without moving code.
- **Form description included** along with section and question descriptions: it uses the same field component and is rendered as markdown by `FormRenderer`, so leaving it out would be inconsistent. Easy to drop if unwanted.
- **Toolbar set**: heading, bold, italic, link, bulleted list, numbered list, quote. These cover what descriptions use; code, tables, images and math are left out to keep the toolbar narrow enough for side-by-side language columns.
- **Icon-only buttons with tooltips**, unlike the email editor's icon+label buttons: two or three language columns side by side leave about 200–400 px each.
- **Toolbar hidden in Preview**: same as GitHub, and there's nothing to format there.
- **Heading inserts `###`**: section names already render as `h2` and question headlines as `h3`, so a description heading shouldn't be larger than its container's title.
- **Edits go through `execCommand('insertText')`** with a direct `onChange` fallback: it's the only way to keep native undo in a textarea, and it keeps the auto-translate debounce firing.
- **Ctrl/⌘+B, I, K shortcuts**: cheap, and what GitHub users expect.
- **No backend change**: storage and API are unaffected.

## 5. Open questions

1. **Editor technology: textarea or CodeMirror?**
   - A: Plain textarea + toolbar + Preview tab (this design). Small, no dependency, matches current behaviour.
   - B: Reuse CodeMirror 6 (`@codemirror/*` is already a dependency, through `LiquidEditor`) with `@codemirror/lang-markdown` for syntax highlighting. More polished, but `LiquidEditor` is tied to the Liquid email schema, so this means a second CodeMirror wrapper, re-implementing disabled/placeholder/resize, and loading CodeMirror on the form editor page (it's currently only on the email pages).
   - Recommendation: A. Descriptions are a few lines; highlighting adds little for that length.

2. **Where does Preview live: one tab per language column, or one toggle for the whole field?**
   - A: Each language column has its own Write/Preview tabs (this design). Like GitHub; you can compare raw English with rendered French.
   - B: One Write/Preview switch in the field's label row flips every language column at once. Less chrome per column and easier to compare rendered translations, but the toolbar then has to live per column anyway, so the header is split in two places.
   - Recommendation: A, because it matches the issue's "like GitHub" and keeps each editor self-contained.

3. **Auto-translate and markdown syntax.** `TranslationService.translate_batch` (`api/app/utils/translation.py`) sends text to Google Translate with `format_='text'`. Google can mangle markdown in that mode, e.g. `**gras **` or translating the visible part of a URL. This design doesn't change translation; the Preview tab makes any damage visible, and the admin fixes it by hand.
   - A: Leave translation as it is (this design).
   - B: Add a follow-up that protects markdown during translation (render to HTML, translate with `format_='html'`, convert back; or mask URLs and markers). That's a backend change to a shared service and needs its own design.
   - Recommendation: A for this issue; open a separate issue for B if maintainers see mangled output in practice.

## 6. Implementation plan

Frontend only. There is no frontend unit-test suite; verify each task with `pnpm run build` in `webapp/` and then in the browser.

### Task 1: Markdown formatting helper

- **Depends on:** none
- **Files:** `webapp/src/components/markdownFormatting.js` (new)
- **Change:** Export `applyFormat(action, value, start, end, placeholderText)` for actions `heading`, `bold`, `italic`, `link`, `bulletList`, `numberedList`, `quote`, following the table and rules in section 3 "Toolbar actions": inline wrap with placeholder and selection, line-prefix across every selected line, toggle off when already applied, numbered lists numbered `1.`, `2.`, …, leading blank line before a block prefix when the previous line is ordinary text. Return `{ replaceStart, replaceEnd, text, selectionStart, selectionEnd }`, where `replaceStart`/`replaceEnd` is the range of `value` to replace (it can be wider than the selection for line actions) and the selection offsets are absolute in the resulting string. No React, no DOM.
- **Acceptance criteria:**
  - `applyFormat('bold', 'hello world', 6, 11, 'bold text')` replaces `world` with `**world**` and leaves `world` selected.
  - `applyFormat('bold', 'ab', 1, 1, 'bold text')` inserts `**bold text**` at offset 1 with `bold text` selected.
  - Applying `bold` to `**world**` (selection covering the markers or just the inner word) removes the markers.
  - `bulletList` on a selection spanning `a\nb\nc` yields `- a\n- b\n- c`; applying it again yields `a\nb\nc`.
  - `numberedList` on `a\nb` yields `1. a\n2. b`.
  - `link` with selection `site` yields `[site](https://)` with `https://` selected.
  - `pnpm run build` passes.
- **Verification:** run the cases above in a quick `node --input-type=module` snippet (or the browser console) and paste the output in the task summary; there is no test runner for the webapp.

### Task 2: `MarkdownEditor` component

- **Depends on:** Task 1
- **Files:** `webapp/src/components/MarkdownEditor.js` (new), `webapp/public/locales/en/translation.json`, `webapp/public/locales/fr/translation.json`
- **Change:** Build the component described in section 3 "Component: `MarkdownEditor`": Write/Preview tabs, icon-only toolbar (hidden in Preview, disabled when `disabled`), textarea with the props listed, Preview via `MarkdownRenderer` wrapped in `previewClassName` with an empty-state message, edits applied with `execCommand('insertText')` and the `onChange` fallback, selection restored afterwards, Ctrl/⌘+B/I/K shortcuts, ARIA roles as in section 3. Add the new i18n keys from section 3 to both locale files (French: `Write` → `Écrire`, `Nothing to preview` → `Rien à prévisualiser`, `Numbered list` → `Liste numérotée`, `Bulleted list` → `Liste à puces`, `Quote` → `Citation`, `italic text` → `texte en italique`, `list item` → `élément de liste`, `quote` → `citation`, `Markdown is supported.` → `Le Markdown est pris en charge.`, `Formatting` → `Mise en forme`). Don't add duplicates of keys that already exist.
- **Acceptance criteria:**
  - The component works standalone as a controlled input: `value`/`onChange` round-trip, `onBlur` fires on textarea blur.
  - Clicking a toolbar button changes the text as Task 1 specifies, and Ctrl/⌘+Z undoes it in Chrome.
  - Preview renders headings, bold, lists, links and quotes using `MarkdownRenderer`; empty value shows "Nothing to preview".
  - With `disabled`, the textarea and toolbar are disabled, the tabs are not.
  - `pnpm run build` passes; both locale files remain valid JSON.
- **Verification:** exercised through scenarios 1–3 once Task 3 is in.

### Task 3: Use the editor for form, section and question descriptions

- **Depends on:** Task 2
- **Files:** `webapp/src/pages/formEditor/components/TranslatableFieldGroup.js`, `webapp/src/pages/formEditor/components/SectionCard.js`, `webapp/src/pages/formEditor/components/QuestionCard.js`, `webapp/src/pages/formEditor/FormEditor.js`, `webapp/src/pages/formEditor/README.md`
- **Change:** Add `markdown` (default `false`) and `previewClassName` props to `TranslatableFieldGroup`. When `markdown && multiline`, render `MarkdownEditor` instead of the textarea, passing value, change handler, blur, placeholder, `disabled || isTranslatingThisField`, `hasError`, `previewClassName` and an `ariaLabel` of `` `${label} (${language.code.toUpperCase()})` ``, and show the `Markdown is supported.` hint under the label. Pass `markdown` and the `previewClassName` from the table in section 3 at the three call sites. Mention the new props in the README's component notes.
- **Acceptance criteria:**
  - Form description, section description and question description show Write/Preview tabs and the toolbar in every language column; section name, question headline, placeholder, option labels and validation fields are unchanged.
  - `AnnouncementsAdmin`, `ProgrammeEditor` and the document pages render exactly as before.
  - Typing in the primary language still auto-translates into empty columns after ~1 s, and a toolbar edit in the primary column also triggers it.
  - Re-translate still works, and the column being translated has its textarea and toolbar disabled while the request runs.
  - Saving the form stores the markdown text unchanged; reloading the editor shows it.
  - `pnpm run build` passes.
- **Verification:** scenarios 1–5.

## 7. Verification scenarios

The seed's `agent-test` event uses new forms and has `en` and `fr`, so both language columns appear. Auto-translate needs Google Translate credentials; in a seeded environment without them, scenario 4 can only check that typing and toolbar edits don't break when translation fails.

| # | Role | Start at | Steps | Expected |
| --- | --- | --- | --- | --- |
| 1 | `event-admin` | `/agent-test/forms/<application form id>/edit` (find the id from the event's form list) | Expand the first section. In the EN Section Description column, type `Intro`, select it, click Bold; click Bulleted list on a new line and type `one`; click Preview. | Text becomes `**Intro**` and `- one`. Preview shows bold "Intro" and a bulleted item, styled like the form renderer. FR column is still on Write. |
| 2 | `event-admin` | same | On a question's Description: with no selection click Link; check the textarea; press Ctrl+Z; then type text, select it and press Ctrl+B; click Bold again with the same selection. | Link inserts `[link text](https://)` with `https://` selected; Ctrl+Z removes it. Ctrl+B wraps in `**`, second Bold removes the markers. |
| 3 | `event-admin` | same | Add markdown to a section description and a question description, Save, reload the page, then open the form preview (`/agent-test/forms/<id>/preview`). | Text persists exactly; the respondent preview renders the same formatting the editor's Preview tab showed. |
| 4 | `event-admin` | same | Type in the EN column of a question description and wait 2 s; then use the toolbar in EN. | With translation configured: the empty FR column fills in and its editor is disabled (toolbar too) only during the request. Without it: no console errors beyond the failed translate call, and the EN editor stays editable. *(Depends on Google Translate.)* |
| 5 | `event-admin` | `/agent-test/announcementsAdmin`, then the form editor's Section Name / Question Headline | Look at the announcement body field and the name/headline fields. | No Write/Preview tabs or toolbar there: unchanged plain inputs/textareas. |
| 6 | `user` (no roles) | `/agent-test/forms/<id>/edit` | Open the URL directly. | Same as today: the form structure API refuses the request (`form_admin_required`), the page shows its load error and no form content or description editors appear. |
| 7 | `event-admin`, 390×844 viewport | form editor | Expand a section. | Language columns stack; tabs and toolbar fit or wrap without overflow or clipped icons. |

## 8. Migration and rollout

None. Frontend only, no schema or data changes, and existing descriptions are already markdown.
