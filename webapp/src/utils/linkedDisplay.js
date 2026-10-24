// Which of a linked form's questions a form shows, from
// `form.settings.linked_display` ({ hidden_section_ids, hidden_question_ids }).
// Everything is shown when the setting is absent. The server applies the same
// rule (api/app/forms/linked_display.py) and strips hidden answers before they
// reach a reviewer; this copy is for the editor and the admin preview.

// Question types with no answer, so never listed or shown.
export const LINKED_DISPLAY_ONLY_TYPES = ['information', 'sub-heading'];

export function getLinkedDisplay(settings) {
  const display = (settings && settings.linked_display) || {};
  return {
    hidden_section_ids: display.hidden_section_ids || [],
    hidden_question_ids: display.hidden_question_ids || [],
  };
}

export function isLinkedQuestionShown(display, sectionId, questionId) {
  return !display.hidden_section_ids.includes(sectionId)
    && !display.hidden_question_ids.includes(questionId);
}

/** `form` without the questions `display` hides, nor sections left empty. */
export function filterLinkedForm(form, display) {
  if (!form) return form;
  const sections = (form.sections || [])
    .map(section => ({
      ...section,
      questions: (section.questions || []).filter(q => isLinkedQuestionShown(display, section.id, q.id)),
    }))
    .filter(section => section.questions.length > 0);
  return { ...form, sections };
}

function collectQuestionIds(expression, ids) {
  if (!expression || typeof expression !== 'object') return ids;
  if (expression.question_id !== undefined && expression.question_id !== '') {
    const id = Number(expression.question_id);
    if (!Number.isNaN(id)) ids.add(id);
  }
  (expression.conditions || []).forEach(c => collectQuestionIds(c, ids));
  return ids;
}

/** Ids of every question the sections' and questions' dependencies refer to. */
export function dependencyQuestionIds(sections) {
  const ids = new Set();
  (sections || []).forEach(section => {
    collectQuestionIds(section.dependency_expression, ids);
    (section.questions || []).forEach(q => collectQuestionIds(q.dependency_expression, ids));
  });
  return ids;
}
