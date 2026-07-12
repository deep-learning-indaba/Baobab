export function generateClientId() {
  return `temp_${Math.random().toString(36).substr(2, 9)}`;
}

export function createEmptySection(languages, order, defaultName = 'Untitled Section') {
  const langObject = languages.reduce((acc, lang) => {
    acc[lang.code] = '';
    return acc;
  }, {});

  const nameObject = languages.reduce((acc, lang) => {
    acc[lang.code] = defaultName;
    return acc;
  }, {});

  return {
    id: generateClientId(),
    order,
    key: '',
    name: nameObject,
    description: langObject,
    questions: [createEmptyQuestion(languages, 1)]
  };
}

export function createEmptyQuestion(languages, order) {
  const langObject = languages.reduce((acc, lang) => {
    acc[lang.code] = '';
    return acc;
  }, {});

  return {
    id: generateClientId(),
    type: null,
    order,
    is_required: false,
    key: '',
    settings: {},
    headline: langObject,
    description: langObject,
    placeholder: langObject,
    validation_regex: langObject,
    validation_text: langObject,
    options: []
  };
}

export function createEmptyOption(languages) {
  const labels = languages.reduce((acc, lang) => {
    acc[lang.code] = '';
    return acc;
  }, {});

  return {
    id: generateClientId(),
    value: '',
    labels
  };
}

export function duplicateSection(section) {
  return {
    ...section,
    id: generateClientId(),
    backendId: undefined,
    questions: section.questions.map(q => duplicateQuestion(q))
  };
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

export function hasChoiceOptions(type) {
  if (!type) return false;
  return ['combobox', 'checkboxes', 'radio', 'single-choice'].includes(type);
}

export function hasPlaceholder(type) {
  if (!type) return false;
  return ['short-text', 'long-text', 'numeric', 'combobox', 'multi-file'].includes(type);
}

export function hasValidation(type) {
  if (!type) return false;
  return ['short-text', 'long-text', 'markdown', 'combobox', 'checkboxes', 'radio', 'single-choice'].includes(type);
}

export function getDefaultSettingsForType(type) {
  switch (type) {
    case 'file':
      return {
        accepted_extensions: [],
        max_file_size_mb: 10
      };
    case 'multi-file':
      return {
        accepted_extensions: [],
        max_file_size_mb: 10,
        max_files: 5
      };
    case 'numeric':
      return {
        decimal_places: 0
      };
    case 'reference':
      return {
        min_referrals: 1,
        max_referrals: 3
      };
    default:
      return {};
  }
}
