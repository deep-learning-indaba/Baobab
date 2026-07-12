export function validateForm(sections, languages, formName = {}) {
  const errors = [];
  const langCodes = languages.map(l => l.code);

  // Validate form name in all languages
  langCodes.forEach(lang => {
    if (!formName[lang] || !formName[lang].trim()) {
      errors.push({
        path: `form.name.${lang}`,
        message: `Form name is required in ${lang.toUpperCase()}`,
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
          message: `Section ${section.order} name is required in ${lang.toUpperCase()}`,
          severity: 'error'
        });
      }
    });

    section.questions.forEach((question, questionIndex) => {
      // Validate question type
      if (!question.type) {
        errors.push({
          path: `sections[${sectionIndex}].questions[${questionIndex}].type`,
          message: `Question ${question.order} in section ${section.order} must have a type`,
          severity: 'error'
        });
      }

      // Validate question headline in all languages (except information type)
      if (question.type !== 'information') {
        langCodes.forEach(lang => {
          if (!question.headline[lang] || !question.headline[lang].trim()) {
            errors.push({
              path: `sections[${sectionIndex}].questions[${questionIndex}].headline.${lang}`,
              message: `Question ${question.order} in section ${section.order} headline is required in ${lang.toUpperCase()}`,
              severity: 'error'
            });
          }
        });
      }

      // Validate options for choice-based questions
      const hasOptions = question.type && ['combobox', 'checkboxes', 'radio', 'single-choice'].includes(question.type);
      if (hasOptions) {
        if (!question.options || question.options.length === 0) {
          errors.push({
            path: `sections[${sectionIndex}].questions[${questionIndex}].options`,
            message: `Question ${question.order} in section ${section.order} must have at least one option`,
            severity: 'error'
          });
        } else {
          const values = new Set();
          
          question.options.forEach((option, optIndex) => {
            // Check for empty values
            if (!option.value || !option.value.trim()) {
              errors.push({
                path: `sections[${sectionIndex}].questions[${questionIndex}].options[${optIndex}].value`,
                message: `Option ${optIndex + 1} in question ${question.order} must have a value`,
                severity: 'error'
              });
            } else {
              // Check for duplicate values
              if (values.has(option.value)) {
                errors.push({
                  path: `sections[${sectionIndex}].questions[${questionIndex}].options[${optIndex}].value`,
                  message: `Option value "${option.value}" is duplicated in question ${question.order}`,
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
                  message: `Option ${optIndex + 1} in question ${question.order} label is required in ${lang.toUpperCase()}`,
                  severity: 'error'
                });
              }
            });
          });
        }
      }

      // Validate settings
      if (question.settings) {
        // File extensions validation
        if (question.settings.accepted_extensions) {
          const extensions = question.settings.accepted_extensions;
          if (extensions.some(ext => !ext.startsWith('.'))) {
            errors.push({
              path: `sections[${sectionIndex}].questions[${questionIndex}].settings.accepted_extensions`,
              message: `File extensions in question ${question.order} must start with a period (e.g., .pdf)`,
              severity: 'error'
            });
          }
        }

        // Numeric min/max validation
        if (question.settings.min_value !== undefined && question.settings.max_value !== undefined) {
          if (question.settings.min_value > question.settings.max_value) {
            errors.push({
              path: `sections[${sectionIndex}].questions[${questionIndex}].settings`,
              message: `Question ${question.order}: minimum value must be less than or equal to maximum value`,
              severity: 'error'
            });
          }
        }

        // Word count validation
        if (question.settings.min_words !== undefined && question.settings.max_words !== undefined) {
          if (question.settings.min_words > question.settings.max_words) {
            errors.push({
              path: `sections[${sectionIndex}].questions[${questionIndex}].settings`,
              message: `Question ${question.order}: minimum words must be less than or equal to maximum words`,
              severity: 'error'
            });
          }
        }

        // Referrals validation
        if (question.settings.min_referrals !== undefined && question.settings.max_referrals !== undefined) {
          if (question.settings.min_referrals > question.settings.max_referrals) {
            errors.push({
              path: `sections[${sectionIndex}].questions[${questionIndex}].settings`,
              message: `Question ${question.order}: minimum referrals must be less than or equal to maximum referrals`,
              severity: 'error'
            });
          }
        }
      }
    });
  });

  return errors;
}

export function hasValidationErrors(errors) {
  return errors.some(e => e.severity === 'error');
}
