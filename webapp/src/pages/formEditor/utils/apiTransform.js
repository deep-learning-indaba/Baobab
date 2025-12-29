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

export function normalizeOptions(optionsByLang, languages) {
  if (!optionsByLang) return [];
  
  const primaryLang = languages[0];
  const primaryOptions = optionsByLang[primaryLang] || [];
  
  return primaryOptions.map((opt, index) => ({
    id: `opt_${Math.random().toString(36).substr(2, 9)}`,
    value: opt.value,
    labels: languages.reduce((acc, lang) => {
      acc[lang] = (optionsByLang[lang] && optionsByLang[lang][index]) ? optionsByLang[lang][index].label : '';
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
        backendToClientIdMap[question.id] = `question_${Math.random().toString(36).substr(2, 9)}`;
      }
    });
  });
  
  // Second pass: Transform sections and questions, using the ID map for dependencies
  return apiSections.map(section => ({
    id: `section_${Math.random().toString(36).substr(2, 9)}`,
    backendId: section.id,
    order: section.order,
    key: section.key || '',
    dependency_expression: mapDependencyExpression(section.dependency_expression, backendToClientIdMap),
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
      dependency_expression: mapDependencyExpression(question.dependency_expression, backendToClientIdMap),
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
      key: section.key || undefined,
      dependency_expression: section.dependency_expression === null ? null : (mapDependencyExpression(section.dependency_expression, clientToBackendIdMap) || undefined),
      name: section.name,
      description: section.description,
      questions: section.questions.map(question => {
        const hasOptions = question.options && Array.isArray(question.options) && question.options.length > 0;
        
        return {
          ...(question.backendId && { id: question.backendId }),
          order: question.order,
          type: question.type,
          is_required: question.is_required,
          key: question.key || undefined,
          settings: Object.keys(question.settings || {}).length > 0 ? question.settings : undefined,
          dependency_expression: question.dependency_expression === null ? null : (mapDependencyExpression(question.dependency_expression, clientToBackendIdMap) || undefined),
          linked_question_id: question.linked_question_id || undefined,
          headline: question.headline,
          description: question.description,
          placeholder: question.placeholder,
          validation_regex: question.validation_regex,
          validation_text: question.validation_text,
          ...(hasOptions && { options: denormalizeOptions(question.options, langCodes) })
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
    linked_form_id: apiData.linked_form_id,
    settings: apiData.settings || { page_per_section: false }
  };
  
  const sections = transformFromApiPayload(apiData.sections || [], languages);
  
  return { form, sections };
}
