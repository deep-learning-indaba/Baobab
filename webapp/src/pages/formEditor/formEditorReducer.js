import {
  createEmptySection,
  createEmptyQuestion,
  createEmptyOption,
  duplicateSection,
  duplicateQuestion,
  moveItem,
  generateClientId,
  hasChoiceOptions,
  settingsForType,
  pruneDependencies
} from './utils/stateUtils';
import { FORM_ACTIONS } from './actionTypes';

export function formEditorReducer(state, action) {
  switch (action.type) {
    case FORM_ACTIONS.SET_FORM_SETTING:
      return {
        ...state,
        form: {
          ...state.form,
          [action.key]: action.lang
            ? { ...state.form[action.key], [action.lang]: action.value }
            : action.value
        },
        ui: { ...state.ui, isDirty: true }
      };

    case FORM_ACTIONS.LOAD_FORM:
      return {
        ...state,
        form: action.payload.form,
        sections: action.payload.sections,
        ui: { 
          ...state.ui, 
          isDirty: false,
          validationErrors: []
        }
      };

    case FORM_ACTIONS.SAVE_FORM_START:
      return {
        ...state,
        ui: { ...state.ui, isSaving: true }
      };

    case FORM_ACTIONS.SAVE_FORM_SUCCESS:
      return {
        ...state,
        form: action.payload.form,
        sections: action.payload.sections,
        ui: {
          ...state.ui,
          isSaving: false,
          isDirty: false,
          validationErrors: []
        }
      };

    case FORM_ACTIONS.SAVE_FORM_ERROR:
      return {
        ...state,
        ui: { ...state.ui, isSaving: false }
      };

    case FORM_ACTIONS.ADD_SECTION: {
      const newSection = createEmptySection(
        state.event.languages,
        state.sections.length + 1
      );
      return {
        ...state,
        sections: [...state.sections, newSection],
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.DELETE_SECTION: {
      const removed = state.sections.find(s => s.id === action.sectionId);
      const removedQuestionIds = new Set((removed ? removed.questions : []).map(q => q.id));
      const sections = pruneDependencies(
        state.sections
          .filter(s => s.id !== action.sectionId)
          .map((s, index) => ({ ...s, order: index + 1 })),
        removedQuestionIds
      );
      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.DUPLICATE_SECTION: {
      const sectionIndex = state.sections.findIndex(s => s.id === action.sectionId);
      if (sectionIndex === -1) return state;

      const duplicated = duplicateSection(state.sections[sectionIndex]);
      const sections = [
        ...state.sections.slice(0, sectionIndex + 1),
        duplicated,
        ...state.sections.slice(sectionIndex + 1)
      ].map((s, index) => ({ ...s, order: index + 1 }));

      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.MOVE_SECTION: {
      const sectionIndex = state.sections.findIndex(s => s.id === action.sectionId);
      if (sectionIndex === -1) return state;

      const sections = moveItem(state.sections, sectionIndex, action.direction);
      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }


    case FORM_ACTIONS.UPDATE_SECTION_FIELD: {
      const sections = state.sections.map(s => {
        if (s.id !== action.sectionId) return s;
        
        if (action.lang) {
          return {
            ...s,
            [action.field]: {
              ...s[action.field],
              [action.lang]: action.value
            }
          };
        }
        
        return { ...s, [action.field]: action.value };
      });

      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.SET_SECTION_DEPENDENCY: {
      const sections = state.sections.map(s =>
        s.id === action.sectionId
          ? { ...s, dependency_expression: action.dependencyExpression }
          : s
      );
      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.SET_SECTION_TAG_EXPRESSION: {
      const sections = state.sections.map(s =>
        s.id === action.sectionId
          ? { ...s, tag_expression: action.tagExpression }
          : s
      );
      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.ADD_QUESTION: {
      const sections = state.sections.map(s => {
        if (s.id !== action.sectionId) return s;
        
        const newQuestion = createEmptyQuestion(
          state.event.languages,
          s.questions.length + 1
        );
        
        return {
          ...s,
          questions: [...s.questions, newQuestion]
        };
      });

      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.DELETE_QUESTION: {
      const sections = pruneDependencies(
        state.sections.map(s => {
          if (s.id !== action.sectionId) return s;

          const questions = s.questions
            .filter(q => q.id !== action.questionId)
            .map((q, index) => ({ ...q, order: index + 1 }));

          return { ...s, questions };
        }),
        // Drop any dependency that referenced the question we just removed.
        new Set([action.questionId])
      );

      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.DUPLICATE_QUESTION: {
      const sections = state.sections.map(s => {
        if (s.id !== action.sectionId) return s;
        
        const questionIndex = s.questions.findIndex(q => q.id === action.questionId);
        if (questionIndex === -1) return s;

        const duplicated = duplicateQuestion(s.questions[questionIndex]);
        const questions = [
          ...s.questions.slice(0, questionIndex + 1),
          duplicated,
          ...s.questions.slice(questionIndex + 1)
        ].map((q, index) => ({ ...q, order: index + 1 }));

        return { ...s, questions };
      });

      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.MOVE_QUESTION: {
      const sections = state.sections.map(s => {
        if (s.id !== action.sectionId) return s;
        
        const questionIndex = s.questions.findIndex(q => q.id === action.questionId);
        if (questionIndex === -1) return s;

        const questions = moveItem(s.questions, questionIndex, action.direction);
        return { ...s, questions };
      });

      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }


    case FORM_ACTIONS.UPDATE_QUESTION_FIELD: {
      const sections = state.sections.map(s => {
        if (s.id !== action.sectionId) return s;
        
        const questions = s.questions.map(q => {
          if (q.id !== action.questionId) return q;
          
          if (action.lang) {
            return {
              ...q,
              [action.field]: {
                ...q[action.field],
                [action.lang]: action.value
              }
            };
          }
          
          return { ...q, [action.field]: action.value };
        });
        
        return { ...s, questions };
      });

      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.SET_QUESTION_TYPE: {
      const sections = state.sections.map(s => {
        if (s.id !== action.sectionId) return s;
        
        const questions = s.questions.map(q => {
          if (q.id !== action.questionId) return q;

          // Options survive a move between choice types (combobox <-> radio <->
          // checkboxes): they mean the same thing and rebuilding a long option
          // list by hand after a type change is pure busywork. Moving to a
          // non-choice type drops them, since they no longer apply.
          const keepOptions =
            hasChoiceOptions(action.questionType) && hasChoiceOptions(q.type);

          return {
            ...q,
            type: action.questionType,
            options: keepOptions ? q.options : [],
            // Carry over only the settings that still mean something for the
            // new type, rather than leaving the old type's keys behind.
            settings: settingsForType(action.questionType, q.settings || {})
          };
        });
        
        return { ...s, questions };
      });

      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.SET_QUESTION_SETTINGS: {
      const sections = state.sections.map(s => {
        if (s.id !== action.sectionId) return s;
        
        const questions = s.questions.map(q =>
          q.id === action.questionId
            ? { ...q, settings: action.settings }
            : q
        );
        
        return { ...s, questions };
      });

      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.SET_QUESTION_DEPENDENCY: {
      const sections = state.sections.map(section => {
        if (section.id !== action.sectionId) return section;
        
        return {
          ...section,
          questions: section.questions.map(q =>
            q.id === action.questionId
              ? { ...q, dependency_expression: action.dependencyExpression }
              : q
          )
        };
      });
      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.SET_QUESTION_TAG_EXPRESSION: {
      const sections = state.sections.map(section => {
        if (section.id !== action.sectionId) return section;
        
        return {
          ...section,
          questions: section.questions.map(q =>
            q.id === action.questionId
              ? { ...q, tag_expression: action.tagExpression }
              : q
          )
        };
      });
      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.ADD_OPTION: {
      const sections = state.sections.map(s => {
        if (s.id !== action.sectionId) return s;
        
        const questions = s.questions.map(q => {
          if (q.id !== action.questionId) return q;
          
          const newOption = action.optionData 
            ? {
                id: generateClientId(),
                value: action.optionData.value,
                labels: action.optionData.labels
              }
            : createEmptyOption(state.event.languages);
          return {
            ...q,
            options: [...q.options, newOption]
          };
        });
        
        return { ...s, questions };
      });

      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.DELETE_OPTION: {
      const sections = state.sections.map(s => {
        if (s.id !== action.sectionId) return s;
        
        const questions = s.questions.map(q => {
          if (q.id !== action.questionId) return q;
          
          return {
            ...q,
            options: q.options.filter(opt => opt.id !== action.optionId)
          };
        });
        
        return { ...s, questions };
      });

      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }

    case FORM_ACTIONS.UPDATE_OPTION: {
      const sections = state.sections.map(s => {
        if (s.id !== action.sectionId) return s;
        
        const questions = s.questions.map(q => {
          if (q.id !== action.questionId) return q;
          
          const options = q.options.map(opt => {
            if (opt.id !== action.optionId) return opt;
            
            if (action.field === 'value') {
              return { ...opt, value: action.value };
            } else if (action.lang) {
              return {
                ...opt,
                labels: {
                  ...opt.labels,
                  [action.lang]: action.value
                }
              };
            }
            return opt;
          });
          
          return { ...q, options };
        });
        
        return { ...s, questions };
      });

      return {
        ...state,
        sections,
        ui: { ...state.ui, isDirty: true }
      };
    }



    case FORM_ACTIONS.SET_VALIDATION_ERRORS:
      return {
        ...state,
        ui: { ...state.ui, validationErrors: action.errors }
      };

    default:
      return state;
  }
}
