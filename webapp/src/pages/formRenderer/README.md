# FormRenderer

A modern, generic form renderer component for the Baobab application. This component renders forms created with the Form Editor and allows end-users to respond to forms and edit existing responses.

## Features

- **All Question Types** - Supports all question types from the generic forms system
- **Dependency Evaluation** - Dynamically shows/hides sections and questions based on dependency expressions
- **Validation** - Real-time and submit-time validation with regex support
- **Page-Per-Section Mode** - Renders each section on a separate page with navigation
- **Single Page Mode** - Renders all sections on one page
- **Draft Saving** - Save responses as drafts before final submission
- **Auto-Save** - Optional automatic draft saving at configurable intervals
- **Confirmation Page** - Review answers before final submission
- **i18n Support** - Full internationalization with translated content
- **Responsive Design** - Works on desktop and mobile devices

## Usage

### Basic Usage

```jsx
import { FormRenderer } from './pages/formRenderer';

function MyFormPage() {
  const handleSubmit = async (data) => {
    const response = await fetch(`/api/forms/${formId}/response`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        answers: data.answers,
        is_submitted: data.is_submitted
      })
    });
    
    if (response.ok) {
      return { success: true, data: await response.json() };
    } else {
      return { success: false, error: 'Failed to submit' };
    }
  };

  const handleSave = async (data) => {
    // Similar to handleSubmit but with is_submitted: false
    return handleSubmit({ ...data, is_submitted: false });
  };

  return (
    <FormRenderer
      form={formData}
      language="en"
      onSubmit={handleSubmit}
      onSave={handleSave}
      onCancel={() => window.history.back()}
    />
  );
}
```

### Editing an Existing Response

```jsx
<FormRenderer
  form={formData}
  response={existingResponse}
  language="en"
  onSubmit={handleSubmit}
  onSave={handleSave}
/>
```

### Page-Per-Section Mode

The form will automatically use page-per-section mode if `form.settings.page_per_section` is `true`:

```jsx
// Form data from API
const formData = {
  id: 1,
  name: { en: 'Application Form' },
  settings: {
    page_per_section: true  // Enable page-per-section mode
  },
  sections: [...]
};
```

### With Auto-Save

```jsx
<FormRenderer
  form={formData}
  language="en"
  onSubmit={handleSubmit}
  onSave={handleSave}
  autoSaveInterval={30000} // Auto-save every 30 seconds
/>
```

### Read-Only Mode

```jsx
<FormRenderer
  form={formData}
  response={submittedResponse}
  language="en"
  readOnly={true}
/>
```

## Props

| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `form` | object | Yes | - | Form definition from the API |
| `response` | object | No | null | Existing response for editing |
| `language` | string | No | 'en' | Current language code |
| `onSubmit` | function | Yes | - | Async callback for form submission |
| `onSave` | function | No | - | Async callback for saving draft |
| `onCancel` | function | No | - | Callback when user cancels |
| `readOnly` | boolean | No | false | Disable all inputs |
| `linkedResponse` | object | No | null | Linked form response (for review forms) |
| `showConfirmation` | boolean | No | true | Show confirmation page before submit |
| `autoSaveInterval` | number | No | 0 | Auto-save interval in ms (0 = disabled) |

## Form Data Structure

The component expects form data in the format returned by the generic forms API:

```javascript
{
  id: 1,
  name: { en: 'My Form', fr: 'Mon Formulaire' },
  is_active: true,
  is_open: true,
  multiple_responses: false,
  settings: {
    page_per_section: false
  },
  sections: [
    {
      id: 1,
      order: 1,
      name: { en: 'Personal Information' },
      description: { en: 'Please provide your details' },
      dependency_expression: null, // or dependency object
      questions: [
        {
          id: 1,
          order: 1,
          type: 'short-text',
          is_required: true,
          headline: { en: 'Full Name' },
          description: { en: 'Enter your full legal name' },
          placeholder: { en: 'John Doe' },
          validation_regex: { en: '^[A-Za-z ]+$' },
          validation_text: { en: 'Only letters and spaces allowed' },
          dependency_expression: null,
          settings: {}
        }
      ]
    }
  ]
}
```

## Response Data Structure

```javascript
{
  id: 1,
  form_id: 1,
  user_id: 123,
  is_submitted: false,
  language: 'en',
  answers: [
    {
      id: 1,
      question_id: 1,
      value: 'John Doe',
      is_active: true
    }
  ]
}
```

## Supported Question Types

| Type | Component | Description |
|------|-----------|-------------|
| `short-text` | FormTextBox | Single-line text input |
| `long-text` | FormTextArea | Multi-line textarea |
| `markdown` | FormTextArea | Markdown-enabled textarea |
| `numeric` | FormTextBox (number) | Number input |
| `combobox` | FormSelect | Dropdown select |
| `checkboxes` | FormMultiCheckbox | Multiple checkboxes |
| `radio` | FormRadio | Radio buttons |
| `single-choice` | FormRadio | Radio buttons (alias) |
| `single-checkbox` | FormCheckbox | Single checkbox |
| `date` | FormDate | Date picker |
| `file` | FormFileUpload | Single file upload |
| `multi-file` | FormMultiFile | Multiple file upload |
| `country` | FormCountry | Country selector with flags |
| `information` | Display only | Information/heading display |
| `sub-heading` | Display only | Sub-heading display |

## Dependency Expressions

The renderer supports complex dependency expressions for conditional visibility:

### Simple Condition
```javascript
{
  question_id: 1,
  operator: 'EQUALS',
  values: ['yes']
}
```

### Complex Condition (AND)
```javascript
{
  operator: 'AND',
  conditions: [
    { question_id: 1, operator: 'EQUALS', values: ['yes'] },
    { question_id: 2, operator: 'IN', values: ['option1', 'option2'] }
  ]
}
```

### Supported Operators

**Comparison:** `EQUALS`, `NOT_EQUALS`, `IN`, `NOT_IN`

**Numeric:** `GREATER_THAN`, `LESS_THAN`, `GREATER_THAN_OR_EQUAL`, `LESS_THAN_OR_EQUAL`, `BETWEEN`

**Text:** `CONTAINS`, `STARTS_WITH`, `ENDS_WITH`, `REGEX`

**Boolean:** `IS_EMPTY`, `IS_NOT_EMPTY`

**Logical:** `AND`, `OR`, `NOT`

## Validation

The renderer validates answers based on:

1. **Required fields** - Checks if required questions have answers
2. **Regex validation** - Validates against `validation_regex` if provided
3. **Option validation** - Ensures selected values are valid options

## Styling

The component uses modern CSS with:

- **Primary color**: `#3b82f6` (blue)
- **Success color**: `#10b981` (green)
- **Error color**: `#ef4444` (red)
- **Warning color**: `#f59e0b` (amber)

Custom styling can be applied by overriding CSS classes:

- `.form-renderer` - Main container
- `.form-header` - Form title area
- `.form-progress` - Progress indicator
- `.form-navigation` - Navigation buttons
- `.section-renderer` - Section container
- `.question-renderer` - Question container

## Dependencies

- React 16.8+ (hooks required)
- react-i18next (translations)
- Existing form controls in `webapp/src/components/form/`
- File service for uploads

## Examples

### Integration with API

```jsx
import React, { useEffect, useState } from 'react';
import { FormRenderer } from './pages/formRenderer';
import { formService } from './services/forms';

function FormPage({ formId }) {
  const [form, setForm] = useState(null);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      const formData = await formService.getForm(formId);
      const responseData = await formService.getResponse(formId);
      setForm(formData);
      setResponse(responseData);
      setLoading(false);
    }
    loadData();
  }, [formId]);

  const handleSubmit = async (data) => {
    try {
      if (response) {
        await formService.updateResponse(formId, response.id, data);
      } else {
        await formService.createResponse(formId, data);
      }
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <FormRenderer
      form={form}
      response={response}
      language="en"
      onSubmit={handleSubmit}
    />
  );
}
```
