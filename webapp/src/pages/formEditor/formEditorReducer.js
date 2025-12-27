import { 
  createEmptySection, 
  createEmptyQuestion,
  createEmptyOption,
  duplicateSection,
  duplicateQuestion,
  moveItem,
  generateClientId
} from './utils/stateUtils';
import { FORM_ACTIONS } from './actionTypes';

export function formEditorReducer(state, action) {
  switch (action.type) {
    case FORM_ACTIONS.SET_FORM_SETTING:
      return {
        ...state,
        form: {
          ...state.form,
          [action.key]: action.value
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
        state.sections.length + 1,
        'Untitled Section'
      );
      return {
        ...state,
        sections: [...state.sections, newSection],
        ui: { ...state.ui, isDirty: true, expandedSections: new Set([...state.ui.expandedSections, newSection.id]) }
      };
    }

    case FORM_ACTIONS.DELETE_SECTION: {
      const sections = state.sections
        .filter(s => s.id !== action.sectionId)
        .map((s, index) => ({ ...s, order: index + 1 }));
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

    case FORM_ACTIONS.REORDER_SECTIONS: {
      const sections = action.sectionIds
        .map(id => state.sections.find(s => s.id === id))
        .filter(Boolean)
        .map((s, index) => ({ ...s, order: index + 1 }));
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
          ? { ...s, dependency_expression: action.expression }
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
      const sections = state.sections.map(s => {
        if (s.id !== action.sectionId) return s;
        
        const questions = s.questions
          .filter(q => q.id !== action.questionId)
          .map((q, index) => ({ ...q, order: index + 1 }));
        
        return { ...s, questions };
      });

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

    case FORM_ACTIONS.REORDER_QUESTIONS: {
      const sections = state.sections.map(s => {
        if (s.id !== action.sectionId) return s;
        
        const questions = action.questionIds
          .map(id => s.questions.find(q => q.id === id))
          .filter(Boolean)
          .map((q, index) => ({ ...q, order: index + 1 }));
        
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
          
          return {
            ...q,
            type: action.questionType,
            options: []
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
      const sections = state.sections.map(s => {
        if (s.id !== action.sectionId) return s;
        
        const questions = s.questions.map(q =>
          q.id === action.questionId
            ? { ...q, dependency_expression: action.expression }
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

    case FORM_ACTIONS.REORDER_OPTIONS: {
      const sections = state.sections.map(s => {
        if (s.id !== action.sectionId) return s;
        
        const questions = s.questions.map(q => {
          if (q.id !== action.questionId) return q;
          
          const options = action.optionIds
            .map(id => q.options.find(opt => opt.id === id))
            .filter(Boolean);
          
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

    case FORM_ACTIONS.TOGGLE_SECTION_EXPANDED: {
      const expandedSections = new Set(state.ui.expandedSections);
      if (expandedSections.has(action.sectionId)) {
        expandedSections.delete(action.sectionId);
      } else {
        expandedSections.add(action.sectionId);
      }
      
      return {
        ...state,
        ui: { ...state.ui, expandedSections }
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
