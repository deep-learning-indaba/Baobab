function mapDependencyExpression(expression, idMap) {
  if (!expression) return expression;

  // If it's a simple condition with a question_id
  if (expression.question_id !== undefined) {
    const mappedId = idMap[expression.question_id];
    return {
      ...expression,
      question_id: mappedId !== undefined ? mappedId : expression.question_id
    };
  }

  // If it's a logical operator (AND, OR, NOT) with conditions
  if (expression.conditions && Array.isArray(expression.conditions)) {
    return {
      ...expression,
      conditions: expression.conditions.map(cond => mapDependencyExpression(cond, idMap))
    };
  }

  return expression;
}

/**
 * Coerce numeric-looking question_id values to numbers.
 *
 * The dependency editor reads question_id out of a <select>, whose value is
 * always a string. For a question in *this* form that's fine - it's a client id
 * that gets mapped to a real id on save. But for a linked form's question the
 * value is already a real database id, so sending it as the string "42" would
 * have the server look up answers_dict["42"] against integer keys, never
 * match, and treat the dependency as unsatisfied.
 */
function normalizeQuestionIdTypes(expression) {
  if (!expression) return expression;

  if (expression.question_id !== undefined) {
    const id = expression.question_id;
    if (typeof id === 'string' && /^\d+$/.test(id)) {
      return { ...expression, question_id: parseInt(id, 10) };
    }
    return expression;
  }

  if (Array.isArray(expression.conditions)) {
    return {
      ...expression,
      conditions: expression.conditions.map(normalizeQuestionIdTypes)
    };
  }

  return expression;
}

function prepareDependencyExpression(expression, idMap) {
  if (expression === null || expression === undefined) return null;
  return normalizeQuestionIdTypes(mapDependencyExpression(expression, idMap));
}

export function normalizeOptions(optionsByLang, languages) {
  if (!optionsByLang) return [];

  const primaryLang = languages[0];
  const primaryOptions = optionsByLang[primaryLang] || [];

  return primaryOptions.map((opt, index) => ({
    id: `opt_${Math.random().toString(36).slice(2, 11)}`,
    value: opt.value,
    labels: languages.reduce((acc, lang) => {
      const langOptions = optionsByLang[lang];
      // Match on value rather than array position. Option order is not
      // guaranteed to be identical across language rows, and a positional
      // match silently pairs an option with the wrong language's label.
      let label = '';
      if (Array.isArray(langOptions)) {
        const byValue = langOptions.find(o => o && o.value === opt.value);
        const fallback = langOptions[index];
        label = (byValue && byValue.label) || (fallback && fallback.label) || '';
      }
      acc[lang] = label;
      return acc;
    }, {})
  }));
}

export function denormalizeOptions(unifiedOptions, languages) {
  return languages.reduce((acc, lang) => {
    acc[lang] = unifiedOptions.map(opt => ({
      value: opt.value,
      label: opt.labels[lang] || ''
    }));
    return acc;
  }, {});
}

export function transformFromApiPayload(apiSections, languages) {
  const langCodes = languages.map(l => l.code);

  // First pass: Build a map from backend IDs to client IDs for all questions
  const backendToClientIdMap = {};
  apiSections.forEach(section => {
    section.questions.forEach(question => {
      if (question.id) {
        backendToClientIdMap[question.id] = `question_${Math.random().toString(36).slice(2, 11)}`;
      }
    });
  });

  // Second pass: Transform sections and questions, using the ID map for dependencies
  return apiSections.map(section => ({
    id: `section_${Math.random().toString(36).slice(2, 11)}`,
    backendId: section.id,
    order: section.order,
    key: section.key || '',
    dependency_expression: mapDependencyExpression(section.dependency_expression, backendToClientIdMap) || null,
    tag_expression: section.tag_expression || null,
    // name and description are now i18n objects from API
    name: section.name || {},
    description: section.description || {},
    questions: section.questions.map(question => ({
      id: backendToClientIdMap[question.id],
      backendId: question.id,
      order: question.order,
      type: question.type,
      is_required: question.is_required,
      key: question.key || '',
      settings: question.settings || {},
      dependency_expression: mapDependencyExpression(question.dependency_expression, backendToClientIdMap) || null,
      tag_expression: question.tag_expression || null,
      linked_question_id: question.linked_question_id,
      // All translatable fields are now i18n objects from API
      headline: question.headline || {},
      description: question.description || {},
      placeholder: question.placeholder || {},
      validation_regex: question.validation_regex || {},
      validation_text: question.validation_text || {},
      options: normalizeOptions(question.options, langCodes)
    }))
  }));
}

export function transformToApiPayload(sections, languages) {
  const langCodes = languages.map(l => l.code);

  // Build a map from client IDs to backend IDs for all questions
  const clientToBackendIdMap = {};
  sections.forEach(section => {
    section.questions.forEach(question => {
      if (question.backendId) {
        clientToBackendIdMap[question.id] = question.backendId;
      }
    });
  });

  return {
    sections: sections.map(section => ({
      ...(section.backendId && { id: section.backendId }),
      order: section.order,
      // Always send these keys, with null meaning "cleared" - omitting a key
      // would let the API fall back to the stored value, making it impossible
      // to ever remove a key, dependency or tag rule once saved.
      key: section.key || null,
      dependency_expression: prepareDependencyExpression(section.dependency_expression, clientToBackendIdMap),
      tag_expression: section.tag_expression || null,
      name: section.name,
      description: section.description,
      questions: section.questions.map(question => {
        const isChoiceType = ['combobox', 'checkboxes', 'radio', 'single-choice'].includes(question.type);

        return {
          ...(question.backendId && { id: question.backendId }),
          ...(!question.backendId && { client_id: question.id }),
          order: question.order,
          type: question.type,
          is_required: question.is_required,
          key: question.key || null,
          settings: question.settings && Object.keys(question.settings).length > 0
            ? question.settings
            : null,
          dependency_expression: prepareDependencyExpression(question.dependency_expression, clientToBackendIdMap),
          tag_expression: question.tag_expression || null,
          linked_question_id: question.linked_question_id || null,
          headline: question.headline,
          description: question.description,
          placeholder: question.placeholder,
          validation_regex: question.validation_regex,
          validation_text: question.validation_text,
          // Sent for every question, empty for non-choice types, so that
          // switching a question away from a choice type actually removes its
          // stored options instead of leaving orphans behind that then reject
          // every free-text answer as an invalid option.
          options: isChoiceType
            ? denormalizeOptions(question.options || [], langCodes)
            : denormalizeOptions([], langCodes)
        };
      })
    }))
  };
}

export function loadFormFromApi(apiData, languages) {
  const form = {
    id: apiData.id,
    name: apiData.name || {},
    description: apiData.description || {},
    is_active: apiData.is_active,
    is_open: apiData.is_open,
    multiple_responses: apiData.multiple_responses,
    // Without these, the settings panel would show defaults instead of what was
    // saved: a form with allow_edits=false would display the toggle as on, and
    // a configured visibility rule would become invisible (and therefore
    // uneditable) after reload.
    allow_edits: apiData.allow_edits !== undefined ? apiData.allow_edits : true,
    visibility_expression: apiData.visibility_expression || null,
    linked_form_id: apiData.linked_form_id,
    settings: apiData.settings || { page_per_section: false }
  };

  const sections = transformFromApiPayload(apiData.sections || [], languages);

  return { form, sections };
}
