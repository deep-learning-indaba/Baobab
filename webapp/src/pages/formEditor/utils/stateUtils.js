export function generateClientId() {
  return `temp_${Math.random().toString(36).slice(2, 11)}`;
}

// A fresh object per field. Sharing one object reference across
// headline/description/placeholder/validation_* would be safe only as long as
// nothing mutates it in place - a single careless mutation would write the
// same text into all of them at once.
function emptyLangObject(languages, value = '') {
  return languages.reduce((acc, lang) => {
    acc[lang.code] = value;
    return acc;
  }, {});
}

export function createEmptySection(languages, order, defaultName = '') {
  return {
    id: generateClientId(),
    order,
    key: '',
    name: emptyLangObject(languages, defaultName),
    description: emptyLangObject(languages),
    dependency_expression: null,
    tag_expression: null,
    questions: [createEmptyQuestion(languages, 1)]
  };
}

export function createEmptyQuestion(languages, order) {
  return {
    id: generateClientId(),
    type: null,
    order,
    is_required: false,
    key: '',
    settings: {},
    dependency_expression: null,
    tag_expression: null,
    headline: emptyLangObject(languages),
    description: emptyLangObject(languages),
    placeholder: emptyLangObject(languages),
    validation_regex: emptyLangObject(languages),
    validation_text: emptyLangObject(languages),
    options: []
  };
}

export function createEmptyOption(languages) {
  return {
    id: generateClientId(),
    value: '',
    labels: emptyLangObject(languages)
  };
}

export function duplicateSection(section) {
  const duplicated = {
    ...section,
    id: generateClientId(),
    backendId: undefined,
    questions: section.questions.map(q => duplicateQuestion(q))
  };
  // Rewrite intra-section dependencies onto the copies. Without this the
  // duplicated questions still pointed at the originals, so editing the copy's
  // trigger question had no effect on the copy's own conditional logic.
  const idMap = {};
  section.questions.forEach((original, index) => {
    idMap[original.id] = duplicated.questions[index].id;
  });
  duplicated.dependency_expression = remapDependencyQuestionIds(
    duplicated.dependency_expression, idMap
  );
  duplicated.questions = duplicated.questions.map(q => ({
    ...q,
    dependency_expression: remapDependencyQuestionIds(q.dependency_expression, idMap)
  }));
  return duplicated;
}

export function duplicateQuestion(question) {
  return {
    ...question,
    id: generateClientId(),
    backendId: undefined,
    options: question.options.map(opt => ({
      ...opt,
      id: generateClientId()
    }))
  };
}

/** Rewrite question_id references in a dependency expression via idMap. */
export function remapDependencyQuestionIds(expression, idMap) {
  if (!expression) return expression;
  if (expression.question_id !== undefined) {
    const mapped = idMap[expression.question_id];
    return mapped === undefined ? expression : { ...expression, question_id: mapped };
  }
  if (Array.isArray(expression.conditions)) {
    return {
      ...expression,
      conditions: expression.conditions.map(c => remapDependencyQuestionIds(c, idMap))
    };
  }
  return expression;
}

/**
 * Remove any condition that references a question in `removedIds`.
 *
 * Without this, deleting a question leaves any dependency pointing at it
 * dangling: the client id has no backend id to map to, so it would be sent to
 * the API as-is and stored as a string question_id that never matches an
 * answer - permanently hiding the dependent question with no way to see why.
 *
 * Returns null when nothing usable is left, which clears the dependency.
 */
export function stripDependenciesOnQuestions(expression, removedIds) {
  if (!expression || !removedIds || removedIds.size === 0) return expression;

  if (expression.question_id !== undefined) {
    return removedIds.has(expression.question_id) ? null : expression;
  }

  if (Array.isArray(expression.conditions)) {
    const conditions = expression.conditions
      .map(c => stripDependenciesOnQuestions(c, removedIds))
      .filter(c => c !== null);
    if (conditions.length === 0) return null;
    // NOT takes exactly one condition; if its subject went away, so does it.
    if (expression.operator === 'NOT' && conditions.length !== 1) return null;
    return { ...expression, conditions };
  }

  return expression;
}

/** Apply dependency cleanup across every section and question in the form. */
export function pruneDependencies(sections, removedIds) {
  if (!removedIds || removedIds.size === 0) return sections;
  return sections.map(section => ({
    ...section,
    dependency_expression: stripDependenciesOnQuestions(section.dependency_expression, removedIds),
    questions: section.questions.map(q => ({
      ...q,
      dependency_expression: stripDependenciesOnQuestions(q.dependency_expression, removedIds)
    }))
  }));
}

export function reorderItems(items, fromIndex, toIndex) {
  const result = [...items];
  const [removed] = result.splice(fromIndex, 1);
  result.splice(toIndex, 0, removed);

  return result.map((item, index) => ({
    ...item,
    order: index + 1
  }));
}

export function moveItem(items, itemIndex, direction) {
  const targetIndex = direction === 'up' ? itemIndex - 1 : itemIndex + 1;

  if (targetIndex < 0 || targetIndex >= items.length) {
    return items;
  }

  return reorderItems(items, itemIndex, targetIndex);
}

// Single source of truth for per-type capabilities, so the definition can't
// drift out of sync with a duplicate copy elsewhere.
export const CHOICE_TYPES = ['combobox', 'checkboxes', 'radio', 'single-choice'];

export function hasChoiceOptions(type) {
  if (!type) return false;
  return CHOICE_TYPES.includes(type);
}

export function hasPlaceholder(type) {
  if (!type) return false;
  return ['short-text', 'long-text', 'markdown', 'numeric', 'combobox', 'multi-file', 'country'].includes(type);
}

export function hasValidation(type) {
  if (!type) return false;
  return ['short-text', 'long-text', 'markdown'].includes(type);
}

export function hasTypeSettings(type) {
  if (!type) return false;
  return ['file', 'multi-file', 'numeric', 'short-text', 'long-text', 'markdown'].includes(type);
}

export function isDisplayOnly(type) {
  return ['sub-heading', 'information'].includes(type);
}

/** Settings keys that mean something for a given question type. */
const SETTINGS_KEYS_BY_TYPE = {
  file: ['accepted_extensions', 'max_file_size_mb'],
  'multi-file': ['accepted_extensions', 'max_file_size_mb', 'max_files'],
  numeric: ['min_value', 'max_value', 'decimal_places', 'weight'],
  'short-text': ['min_words', 'max_words'],
  'long-text': ['min_words', 'max_words'],
  markdown: ['min_words', 'max_words'],
  reference: ['min_referrals', 'max_referrals'],
  country: ['countryOptions']
};

/**
 * Settings for `type`, carrying over any key that still applies.
 *
 * Without this, changing a question's type would leave the old type's settings
 * in place - e.g. a question switched from File to Numeric would keep
 * `accepted_extensions`, which then trips the editor's file-extension
 * validation on a numeric question.
 */
export function settingsForType(type, existingSettings = {}) {
  const allowed = SETTINGS_KEYS_BY_TYPE[type] || [];
  const next = {};
  allowed.forEach(key => {
    if (existingSettings[key] !== undefined) next[key] = existingSettings[key];
  });
  if (type === 'country' && !next.countryOptions) {
    next.countryOptions = { regions: [], countries: [], excludeCountries: [] };
  }
  return next;
}
