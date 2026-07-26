import { CHOICE_TYPES } from './stateUtils';

// Messages are built through `t` so they are translatable and so the summary in
// the editor reads in the admin's own language. `t` is optional to keep the
// function usable from tests without an i18n instance.
const identity = (key, params) =>
  key.replace(/\{\{(\w+)\}\}/g, (_, name) => (params && params[name] !== undefined ? params[name] : ''));

export function validateForm(sections, languages, formName = {}, t) {
  const translate = t || identity;
  const errors = [];
  const langCodes = languages.map(l => l.code);
  const langLabel = (code) => {
    const match = languages.find(l => l.code === code);
    return match ? match.description || code.toUpperCase() : code.toUpperCase();
  };

  // Validate form name in all languages
  langCodes.forEach(lang => {
    if (!formName[lang] || !formName[lang].trim()) {
      errors.push({
        path: `form.name.${lang}`,
        message: translate('Form name is required in {{language}}', { language: langLabel(lang) }),
        severity: 'error'
      });
    }
  });

  sections.forEach((section, sectionIndex) => {
    // Validate section name in all languages
    langCodes.forEach(lang => {
      if (!section.name[lang] || !section.name[lang].trim()) {
        errors.push({
          path: `sections[${sectionIndex}].name.${lang}`,
          message: translate('Section {{section}}: name is required in {{language}}', {
            section: section.order, language: langLabel(lang)
          }),
          severity: 'error'
        });
      }
    });

    section.questions.forEach((question, questionIndex) => {
      const where = translate('Section {{section}}, question {{question}}', {
        section: section.order, question: question.order
      });

      // Validate question type
      if (!question.type) {
        errors.push({
          path: `sections[${sectionIndex}].questions[${questionIndex}].type`,
          message: translate('{{where}}: choose a question type', { where }),
          severity: 'error'
        });
      }

      // Validate question headline in all languages (except information type)
      if (question.type !== 'information') {
        langCodes.forEach(lang => {
          if (!question.headline[lang] || !question.headline[lang].trim()) {
            errors.push({
              path: `sections[${sectionIndex}].questions[${questionIndex}].headline.${lang}`,
              message: translate('{{where}}: headline is required in {{language}}', {
                where, language: langLabel(lang)
              }),
              severity: 'error'
            });
          }
        });
      }

      // Validate options for choice-based questions
      if (question.type && CHOICE_TYPES.includes(question.type)) {
        if (!question.options || question.options.length === 0) {
          errors.push({
            path: `sections[${sectionIndex}].questions[${questionIndex}].options`,
            message: translate('{{where}}: add at least one option', { where }),
            severity: 'error'
          });
        } else {
          const values = new Set();

          question.options.forEach((option, optIndex) => {
            // Check for empty values
            if (!option.value || !option.value.trim()) {
              errors.push({
                path: `sections[${sectionIndex}].questions[${questionIndex}].options[${optIndex}].value`,
                message: translate('{{where}}: option {{option}} needs a value', { where, option: optIndex + 1 }),
                severity: 'error'
              });
            } else {
              // Check for duplicate values
              if (values.has(option.value)) {
                errors.push({
                  path: `sections[${sectionIndex}].questions[${questionIndex}].options[${optIndex}].value`,
                  message: translate('{{where}}: option value "{{value}}" is used more than once', {
                    where, value: option.value
                  }),
                  severity: 'error'
                });
              }
              values.add(option.value);
            }

            // Check labels in all languages
            langCodes.forEach(lang => {
              if (!option.labels || !option.labels[lang] || !option.labels[lang].trim()) {
                errors.push({
                  path: `sections[${sectionIndex}].questions[${questionIndex}].options[${optIndex}].labels.${lang}`,
                  message: translate('{{where}}: option {{option}} needs a label in {{language}}', {
                    where, option: optIndex + 1, language: langLabel(lang)
                  }),
                  severity: 'error'
                });
              }
            });
          });
        }
      }

      // Validate settings only against the settings that apply to the question's
      // current type (the reducer prunes settings on a type change), so a
      // numeric question is never failed for leftover file-extension settings.
      const settings = question.settings || {};

      if (['file', 'multi-file'].includes(question.type) && settings.accepted_extensions) {
        const bad = settings.accepted_extensions.filter(ext => !ext.startsWith('.'));
        if (bad.length > 0) {
          errors.push({
            path: `sections[${sectionIndex}].questions[${questionIndex}].settings.accepted_extensions`,
            message: translate('{{where}}: file extensions must start with a period (e.g. .pdf)', { where }),
            severity: 'error'
          });
        }
      }

      const rangeChecks = [
        ['min_value', 'max_value', translate('minimum value must not exceed the maximum')],
        ['min_words', 'max_words', translate('minimum words must not exceed the maximum')],
        ['min_referrals', 'max_referrals', translate('minimum referrals must not exceed the maximum')]
      ];
      rangeChecks.forEach(([minKey, maxKey, detail]) => {
        const min = settings[minKey];
        const max = settings[maxKey];
        if (min !== undefined && max !== undefined && Number(min) > Number(max)) {
          errors.push({
            path: `sections[${sectionIndex}].questions[${questionIndex}].settings.${minKey}`,
            message: `${where}: ${detail}`,
            severity: 'error'
          });
        }
      });

      // A regex that cannot compile would silently pass every answer through.
      langCodes.forEach(lang => {
        const pattern = question.validation_regex && question.validation_regex[lang];
        if (!pattern) return;
        try {
          new RegExp(pattern); // eslint-disable-line no-new
        } catch (e) {
          errors.push({
            path: `sections[${sectionIndex}].questions[${questionIndex}].validation_regex.${lang}`,
            message: translate('{{where}}: the {{language}} validation pattern is not a valid regular expression', {
              where, language: langLabel(lang)
            }),
            severity: 'error'
          });
        }
      });

      if (question.type === 'linked-form-question' && !question.linked_question_id) {
        errors.push({
          path: `sections[${sectionIndex}].questions[${questionIndex}].linked_question_id`,
          message: translate('{{where}}: select a question from the linked form', { where }),
          severity: 'error'
        });
      }
    });
  });

  return errors;
}

export function hasValidationErrors(errors) {
  return errors.some(e => e.severity === 'error');
}
