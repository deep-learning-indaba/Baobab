import { MULTI_VALUE_SEPARATOR } from './validation';

const SINGLE_CHOICE_TYPES = ['combobox', 'multi-choice', 'dropdown', 'radio', 'single-choice'];
const MULTI_CHOICE_TYPES = ['checkboxes', 'multi-checkbox'];

/** Option list for a question, in either the API or editor shape. */
export function optionsForQuestion(question, language) {
  const options = question && question.options;
  if (!options) return [];
  if (Array.isArray(options)) {
    return options.map(o => ({
      value: o.value,
      label: o.labels
        ? (o.labels[language] || o.labels.en || Object.values(o.labels)[0] || o.value)
        : (o.label || o.value)
    }));
  }
  const byLang = options[language] || options.en || Object.values(options)[0] || [];
  return Array.isArray(byLang) ? byLang.map(o => ({ value: o.value, label: o.label || o.value })) : [];
}

/**
 * Human-readable rendering of a stored answer value.
 *
 * Answers are stored as opaque strings - option *values*, 'true'/'false' for
 * checkboxes, JSON for files. Showing those verbatim meant review screens
 * displayed things like "p" and "true" instead of "Pea" and "Yes".
 */
export function formatAnswerForDisplay(question, value, language, t) {
  if (value === null || value === undefined || value === '') return null;

  const type = question && question.type;

  if (SINGLE_CHOICE_TYPES.includes(type)) {
    const match = optionsForQuestion(question, language).find(o => o.value === value);
    return match ? match.label : value;
  }

  if (MULTI_CHOICE_TYPES.includes(type)) {
    const options = optionsForQuestion(question, language);
    return String(value)
      .split(MULTI_VALUE_SEPARATOR)
      .map(v => v.trim())
      .filter(Boolean)
      .map(v => {
        const match = options.find(o => o.value === v);
        return match ? match.label : v;
      })
      .join(', ');
  }

  if (type === 'single-checkbox') {
    return value === 'true' || value === true ? t('Yes') : t('No');
  }

  if (type === 'file' || type === 'multi-file') {
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) return parsed.map(f => f.name || f.rename).filter(Boolean).join(', ');
      if (parsed && (parsed.rename || parsed.filename)) return parsed.rename || parsed.filename;
    } catch (e) {
      // not JSON - fall through and show the raw value
    }
    return value;
  }

  if (type === 'date') {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString();
  }

  return value;
}
