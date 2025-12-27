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
  
  return apiSections.map(section => ({
    id: `section_${Math.random().toString(36).substr(2, 9)}`,
    backendId: section.id,
    order: section.order,
    key: section.key || '',
    dependency_expression: section.dependency_expression,
    // name and description are now i18n objects from API
    name: section.name || {},
    description: section.description || {},
    questions: section.questions.map(question => ({
      id: `question_${Math.random().toString(36).substr(2, 9)}`,
      backendId: question.id,
      order: question.order,
      type: question.type,
      is_required: question.is_required,
      key: question.key || '',
      settings: question.settings || {},
      dependency_expression: question.dependency_expression,
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
  
  return {
    sections: sections.map(section => ({
      ...(section.backendId && { id: section.backendId }),
      order: section.order,
      key: section.key || undefined,
      dependency_expression: section.dependency_expression || undefined,
      name: section.name,
      description: section.description,
      questions: section.questions.map(question => {
        const hasOptions = question.options && question.options.length > 0;
        
        return {
          ...(question.backendId && { id: question.backendId }),
          order: question.order,
          type: question.type,
          is_required: question.is_required,
          key: question.key || undefined,
          settings: Object.keys(question.settings).length > 0 ? question.settings : undefined,
          dependency_expression: question.dependency_expression || undefined,
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
    is_active: apiData.is_active,
    is_open: apiData.is_open,
    multiple_responses: apiData.multiple_responses,
    linked_form_id: apiData.linked_form_id,
    settings: apiData.settings || { page_per_section: false }
  };
  
  const sections = transformFromApiPayload(apiData.sections || [], languages);
  
  return { form, sections };
}
