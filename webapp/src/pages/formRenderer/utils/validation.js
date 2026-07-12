/**
 * Validation utilities for form renderer
 */

/**
 * Validate a single answer against question rules
 * @param {object} question - The question object
 * @param {string} value - The answer value
 * @param {string} language - Current language code
 * @param {function} t - Translation function
 * @returns {string|null} Error message or null if valid
 */
export function validateAnswer(question, value, language, t) {
  const translation = getQuestionTranslation(question, language);
  
  // Required check
  if (question.is_required && (!value || (typeof value === 'string' && value.trim() === ''))) {
    return t('This field is required');
  }
  
  // Skip further validation if empty and not required
  if (!value || (typeof value === 'string' && value.trim() === '')) {
    return null;
  }
  
  // Regex validation
  const validationRegex = (translation && translation.validation_regex) || (question.validation_regex && question.validation_regex[language]);
  if (validationRegex) {
    try {
      if (!new RegExp(validationRegex).test(value)) {
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
    const selectedValues = value.split(' ; ').map(v => v.trim());
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
