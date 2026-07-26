/**
 * Validation utilities for form renderer
 */

// Multi-select answers are stored as a single separator-joined string. Shared
// with the backend (see MULTI_VALUE_SEPARATOR in app/forms/models.py).
export const MULTI_VALUE_SEPARATOR = ' ; ';

// Types that render no input, so they can never hold an answer and must never
// be treated as required.
const DISPLAY_ONLY_TYPES = ['information', 'sub-heading', 'linked-form-question'];

// Types whose stored value is a boolean-ish string.
const BOOLEAN_TYPES = ['single-checkbox'];

/**
 * Whether a value counts as "no answer" for this question type.
 *
 * An unticked single-checkbox stores the string 'false', which is truthy - so
 * without this, a required consent checkbox would pass validation while
 * unticked.
 */
export function isBlankAnswer(questionType, value) {
  if (value === null || value === undefined) return true;
  if (typeof value === 'boolean') return questionType && BOOLEAN_TYPES.includes(questionType) ? !value : false;
  if (typeof value !== 'string') return false;
  const trimmed = value.trim();
  if (trimmed === '') return true;
  if (questionType && BOOLEAN_TYPES.includes(questionType)) {
    return ['false', '0', 'no'].includes(trimmed.toLowerCase());
  }
  return false;
}

export function countWords(text) {
  if (!text) return 0;
  return String(text).trim().split(/\s+/).filter(Boolean).length;
}

/**
 * Validate a single answer against question rules
 * @param {object} question - The question object
 * @param {string} value - The answer value
 * @param {string} language - Current language code
 * @param {function} t - Translation function
 * @returns {string|null} Error message or null if valid
 */
export function validateAnswer(question, value, language, t) {
  if (DISPLAY_ONLY_TYPES.includes(question.type)) return null;

  const translation = getQuestionTranslation(question, language);
  const settings = question.settings || {};
  const blank = isBlankAnswer(question.type, value);

  // Required check
  if (question.is_required && blank) {
    return t('This field is required');
  }

  // Skip further validation if empty and not required
  if (blank) {
    return null;
  }

  // Numeric bounds are configurable per question, so they need enforcing here
  // as well as on the server.
  if (question.type === 'numeric' || question.type === 'numeric-text') {
    const numeric = parseFloat(value);
    if (Number.isNaN(numeric)) {
      return t('Enter a number');
    }
    if (settings.min_value !== undefined && settings.min_value !== null && numeric < Number(settings.min_value)) {
      return t('Enter a number of at least {{min}}', { min: settings.min_value });
    }
    if (settings.max_value !== undefined && settings.max_value !== null && numeric > Number(settings.max_value)) {
      return t('Enter a number no greater than {{max}}', { max: settings.max_value });
    }
  }

  // Word count bounds, enforced directly rather than via a generated regex
  // pattern - a pattern like `^(\b\w+\b\s*){3,10}$` can't account for
  // punctuation or accented characters, and would reject most real prose.
  if (['short-text', 'long-text', 'markdown'].includes(question.type)) {
    const hasMin = settings.min_words !== undefined && settings.min_words !== null;
    const hasMax = settings.max_words !== undefined && settings.max_words !== null;
    if (hasMin || hasMax) {
      const words = countWords(value);
      if (hasMin && words < Number(settings.min_words)) {
        return t('Enter at least {{min}} words (currently {{count}})', {
          min: settings.min_words, count: words
        });
      }
      if (hasMax && words > Number(settings.max_words)) {
        return t('Enter no more than {{max}} words (currently {{count}})', {
          max: settings.max_words, count: words
        });
      }
    }
  }

  // Regex validation
  const validationRegex = (translation && translation.validation_regex) || (question.validation_regex && question.validation_regex[language]);
  if (validationRegex) {
    try {
      // Anchored so the whole answer must match, mirroring the server's
      // re.fullmatch - an unanchored test would accept e.g. "abc1234" against
      // `[0-9]{4}`, which the server would then reject.
      if (!new RegExp(`^(?:${validationRegex})$`).test(value)) {
        return (translation && translation.validation_text) || (question.validation_text && question.validation_text[language]) || t('Invalid format');
      }
    } catch (e) {
      console.warn('Invalid validation regex:', e);
    }
  }

  // Options validation for choice-based questions
  const options = (translation && translation.options) || (question.options && question.options[language]);
  if (options && Array.isArray(options) && options.length > 0) {
    const validValues = options.map(opt => opt.value);
    const selectedValues = String(value).split(MULTI_VALUE_SEPARATOR).map(v => v.trim());
    const allValid = selectedValues.every(v => validValues.includes(v));
    if (!allValid) {
      return t('Invalid option selected');
    }
  }

  return null;
}

/**
 * Get question translation for a specific language
 */
function getQuestionTranslation(question, language) {
  // If question has direct translation fields as i18n objects
  if (question.headline && typeof question.headline === 'object') {
    return {
      headline: question.headline[language],
      description: question.description && question.description[language],
      placeholder: question.placeholder && question.placeholder[language],
      validation_regex: question.validation_regex && question.validation_regex[language],
      validation_text: question.validation_text && question.validation_text[language],
      options: question.options && question.options[language]
    };
  }

  // Already flat structure
  return question;
}

/**
 * Validate all answers in a form
 * @param {Array} sections - Array of section objects
 * @param {Array} answers - Array of answer objects
 * @param {object} answersDict - Dictionary of question_id to value
 * @param {string} language - Current language code
 * @param {function} t - Translation function
 * @param {function} isVisible - Function to check if question is visible
 * @returns {object} Dictionary of question_id to error message
 */
export function validateAllAnswers(sections, answers, answersDict, language, t, isVisible) {
  const errors = {};

  sections.forEach(section => {
    if (!section.questions) return;

    section.questions.forEach(question => {
      // Only validate visible questions
      if (isVisible && !isVisible(question, section)) {
        return;
      }

      const value = answersDict[question.id];
      const error = validateAnswer(question, value, language, t);

      if (error) {
        errors[question.id] = error;
      }
    });
  });

  return errors;
}

/**
 * Check if there are any validation errors
 */
export function hasErrors(errors) {
  return Object.keys(errors).length > 0;
}

/**
 * Get error count
 */
export function getErrorCount(errors) {
  return Object.keys(errors).length;
}

/** Question id of the first error in document order, for scroll-to-error. */
export function firstErrorQuestionId(sections, errors) {
  for (const section of sections) {
    for (const question of section.questions || []) {
      if (errors[question.id]) return question.id;
    }
  }
  return null;
}
