# Form Editor

A unified form editing UI component that supports all features available in the generic forms backend.

## Features

- **Inline i18n editing** - All translatable fields show input boxes for each event language side-by-side
- **Unified options** - Options have a shared value across languages with only labels translated
- **Settings vs Options separation** - Question-specific settings stored separately from choice options
- **Type-specific editors** - Specialized settings editors for files, numeric, text, references
- **Full validation** - Client-side validation with detailed error messages
- **Question types** - Support for all question types including renamed types (combobox, checkboxes)
- **State management** - Reducer-based state management

## Usage

```jsx
import { FormEditor } from './pages/formEditor';

function MyFormPage() {
  const languages = [
    { code: 'en', description: 'English' },
    { code: 'fr', description: 'French' }
  ];

  const handleSave = async (formData) => {
    // Make API call to save form
    const response = await fetch(`/api/forms/${formData.id}/structure`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });
    
    if (response.ok) {
      return { success: true, data: await response.json() };
    } else {
      return { success: false, error: 'Failed to save' };
    }
  };

  const handleCancel = () => {
    // Navigate back or close editor
    window.history.back();
  };

  return (
    <FormEditor
      eventId={123}
      formId={456} // undefined for new form
      languages={languages}
      onSave={handleSave}
      onCancel={handleCancel}
      includeReviewTypes={false} // true for review forms
      initialData={null} // or loaded form data
    />
  );
}
```

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `eventId` | number | Yes | Event ID this form belongs to |
| `formId` | number | No | Form ID for editing existing form |
| `languages` | Language[] | Yes | Array of language objects with code and description |
| `onSave` | function | Yes | Async callback for saving form, receives form data |
| `onCancel` | function | Yes | Callback when user cancels editing |
| `includeReviewTypes` | boolean | No | Include review-specific question types (default: false) |
| `initialData` | object | No | Initial form data for editing existing form |

## API Integration

### Loading a Form

```javascript
import { loadFormFromApi } from './pages/formEditor';

// Fetch from API
const response = await fetch(`/api/forms/${formId}/structure`);
const apiData = await response.json();

// Transform to editor format
const { form, sections } = loadFormFromApi(apiData, languages);
```

### Saving a Form

```javascript
import { transformToApiPayload } from './pages/formEditor';

// In your onSave handler
const handleSave = async (editorState) => {
  const payload = transformToApiPayload(editorState.sections, languages);
  
  const formData = {
    is_open: editorState.form.is_open,
    is_active: editorState.form.is_active,
    multiple_responses: editorState.form.multiple_responses,
    settings: editorState.form.settings,
    ...payload
  };
  
  // POST or PUT to API
  const response = await fetch(`/api/forms/${formId}/structure`, {
    method: 'PUT',
    body: JSON.stringify(formData)
  });
  
  return { 
    success: response.ok, 
    data: await response.json() 
  };
};
```

## Components

### TranslatableFieldGroup
Displays input fields for each language side-by-side.

### OptionsEditor
Manages options with unified values and translated labels.

### QuestionTypeSelector
Dropdown for selecting question types with icons.

### QuestionCard
Complete question editor with type-specific settings.

### SectionCard
Section container with collapsible questions.

### FormSettingsPanel
Slide-out panel for form-level settings.

## State Management

The editor uses a reducer pattern with the following actions:

- Form-level: `SET_FORM_SETTING`, `LOAD_FORM`, `SAVE_FORM_START/SUCCESS/ERROR`
- Sections: `ADD_SECTION`, `DELETE_SECTION`, `DUPLICATE_SECTION`, `MOVE_SECTION`, `UPDATE_SECTION_FIELD`, `SET_SECTION_DEPENDENCY`, `SET_SECTION_TAG_EXPRESSION`
- Questions: `ADD_QUESTION`, `DELETE_QUESTION`, `DUPLICATE_QUESTION`, `MOVE_QUESTION`, `UPDATE_QUESTION_FIELD`, `SET_QUESTION_TYPE`, `SET_QUESTION_SETTINGS`, `SET_QUESTION_DEPENDENCY`, `SET_QUESTION_TAG_EXPRESSION`
- Options: `ADD_OPTION`, `DELETE_OPTION`, `UPDATE_OPTION`
- UI: `SET_VALIDATION_ERRORS`

Deleting a question or section also strips any dependency expression that
referenced it (`pruneDependencies` in `utils/stateUtils.js`) - a dangling
reference would otherwise be saved and permanently hide the dependent question.

## Validation

The editor validates:
- Form and section names in all languages (required)
- Question headlines in all languages (required)
- Question types (required)
- Option values (required, unique)
- Option labels in all languages (required)
- Settings constraints (min ≤ max, valid file extensions) for settings that
  apply to the question's current type
- That any `validation_regex` compiles
- That a `linked-form-question` has a question selected

Errors are listed individually in the banner at the top of the editor, and
required fields are highlighted once a save has been attempted.

## Question Types

### Renamed Types
- `multi-choice` → `combobox` (dropdown select)
- `multi-checkbox` → `checkboxes` (multiple checkboxes)

### All Supported Types
- `short-text` - Single-line text
- `long-text` - Multi-line textarea
- `markdown` - Markdown-enabled textarea
- `single-choice` - Radio buttons
- `combobox` - Dropdown select
- `checkboxes` - Multiple checkboxes
- `radio` - Radio buttons (for review scores, review forms only)
- `single-checkbox` - Single checkbox
- `file` - File upload
- `multi-file` - Multiple file upload
- `date` - Date picker
- `numeric` - Number input
- `country` - Country selector
- `sub-heading` - Decorative heading
- `linked-form-question` - Displays an answer from the linked form
- `information` - Information display (review forms only)

### Not offered
- `reference` - the reference-request flow is still tied to the legacy response
  model and has no implementation in `formRenderer`, so it is not offered for new
  questions. Existing questions of this type keep it selectable so that editing
  such a form doesn't silently change it.

## Settings vs Options

**Options** - Only for choice-based questions (combobox, checkboxes, radio, single-choice):
```json
{
  "options": [
    {
      "id": "temp_abc123",
      "value": "option_1",
      "labels": {
        "en": "Option One",
        "fr": "Option Un"
      }
    }
  ]
}
```

**Settings** - For question-specific configuration:
```json
{
  "settings": {
    "accepted_extensions": [".pdf", ".doc"],
    "max_file_size_mb": 10,
    "min_value": 0,
    "max_value": 100,
    "weight": 1.5
  }
}
```

## Styling

Tailwind utilities against the design tokens in `webapp/src/App.css`
(`--clr-primary`, `--clr-action`, `--clr-error`, ...). Don't hard-code colours.

Note the root element carries `text-left`: an unscoped `.container-fluid`
rule elsewhere in the app sets `text-align: -webkit-center`, and without the
override every label in here renders centred over its left-aligned input.

All components are responsive and work on mobile devices.

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Dependencies

- React 16.8+ (hooks required)
- react-i18next (for translations)
- react-select (for dropdown selects)
- Font Awesome (for icons)
