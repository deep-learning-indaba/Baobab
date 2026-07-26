import React, { useState, memo } from 'react';
import TranslatableFieldGroup from './TranslatableFieldGroup';
import QuestionTypeSelector from './QuestionTypeSelector';
import OptionsEditor from './OptionsEditor';
import QuestionSettingsEditor from './QuestionSettingsEditor';
import CountryEditor from './CountryEditor';
import DependencyEditor from './DependencyEditor';
import VisibilityExpressionEditor from './VisibilityExpressionEditor';
import LinkedQuestionSelector from './LinkedQuestionSelector';
import { FORM_ACTIONS } from '../actionTypes';
import {
  hasChoiceOptions,
  hasPlaceholder as typeHasPlaceholder,
  hasValidation as typeHasValidation,
  hasTypeSettings,
  isDisplayOnly
} from '../utils/stateUtils';

const QuestionCard = memo(({
  question,
  sectionId,
  sectionOrder,
  questionIndex,
  totalQuestions,
  languages,
  dispatch,
  t,
  includeReviewTypes = false,
  allQuestions = [],
  linkedFormId = null,
  autoTranslateEnabled = true,
  showErrors = false,
  eventId = null
}) => {
  const [showKey, setShowKey] = useState(!!question.key);
  const [showValidation, setShowValidation] = useState(
    !!question.validation_regex && Object.values(question.validation_regex).some(v => v)
  );
  const [showDependency, setShowDependency] = useState(!!question.dependency_expression);
  const [showTagExpression, setShowTagExpression] = useState(!!question.tag_expression);

  const handleFieldChange = (field, lang, value) =>
    dispatch({ type: FORM_ACTIONS.UPDATE_QUESTION_FIELD, sectionId, questionId: question.id, field, lang, value });

  const handleTypeChange = (type) =>
    dispatch({ type: FORM_ACTIONS.SET_QUESTION_TYPE, sectionId, questionId: question.id, questionType: type });

  const handleRequiredToggle = () =>
    dispatch({ type: FORM_ACTIONS.UPDATE_QUESTION_FIELD, sectionId, questionId: question.id, field: 'is_required', value: !question.is_required });

  const handleSettingsChange = (settings) =>
    dispatch({ type: FORM_ACTIONS.SET_QUESTION_SETTINGS, sectionId, questionId: question.id, settings });

  const handleDependencyChange = (dependencyExpression) =>
    dispatch({ type: FORM_ACTIONS.SET_QUESTION_DEPENDENCY, sectionId, questionId: question.id, dependencyExpression });

  const handleTagExpressionChange = (tagExpression) =>
    dispatch({ type: FORM_ACTIONS.SET_QUESTION_TAG_EXPRESSION, sectionId, questionId: question.id, tagExpression });

  const handleAddOption = (optionData) =>
    dispatch({ type: FORM_ACTIONS.ADD_OPTION, sectionId, questionId: question.id, optionData });

  const handleDeleteOption = (optionId) =>
    dispatch({ type: FORM_ACTIONS.DELETE_OPTION, sectionId, questionId: question.id, optionId });

  const handleUpdateOptionValue = (optionId, value) =>
    dispatch({ type: FORM_ACTIONS.UPDATE_OPTION, sectionId, questionId: question.id, optionId, field: 'value', value });

  const handleUpdateOptionLabel = (optionId, lang, value) =>
    dispatch({ type: FORM_ACTIONS.UPDATE_OPTION, sectionId, questionId: question.id, optionId, field: 'label', lang, value });

  const handleDelete = () => {
    if (window.confirm(t('Are you sure you want to delete this question?'))) {
      dispatch({ type: FORM_ACTIONS.DELETE_QUESTION, sectionId, questionId: question.id });
    }
  };

  const handleDuplicate = () =>
    dispatch({ type: FORM_ACTIONS.DUPLICATE_QUESTION, sectionId, questionId: question.id });

  const handleMoveUp = () =>
    dispatch({ type: FORM_ACTIONS.MOVE_QUESTION, sectionId, questionId: question.id, direction: 'up' });

  const handleMoveDown = () =>
    dispatch({ type: FORM_ACTIONS.MOVE_QUESTION, sectionId, questionId: question.id, direction: 'down' });

  // Unchecking one of these toggles clears the underlying value rather than just
  // hiding its editor - otherwise a hidden regex or dependency stays saved and
  // enforced, so turning "Add Validation" off wouldn't stop the form rejecting
  // answers against a rule the admin can no longer see.
  const toggleValidation = () => {
    if (showValidation) {
      languages.forEach(lang => {
        handleFieldChange('validation_regex', lang.code, '');
        handleFieldChange('validation_text', lang.code, '');
      });
    }
    setShowValidation(!showValidation);
  };

  const toggleDependency = () => {
    if (showDependency) handleDependencyChange(null);
    setShowDependency(!showDependency);
  };

  const toggleTagExpression = () => {
    if (showTagExpression) handleTagExpressionChange(null);
    setShowTagExpression(!showTagExpression);
  };

  const toggleKey = () => {
    if (showKey) handleFieldChange('key', null, '');
    setShowKey(!showKey);
  };

  const showOptions = hasChoiceOptions(question.type);
  const showPlaceholder = typeHasPlaceholder(question.type);
  const showSettings = hasTypeSettings(question.type);
  const hasCountrySettings = question.type === 'country';
  const hasLinkedQuestion = question.type === 'linked-form-question';
  const canHaveValidation = typeHasValidation(question.type);
  const displayOnly = isDisplayOnly(question.type);

  const isFirst = questionIndex === 0;
  const isLast = questionIndex === totalQuestions - 1;

  const iconBtn = "p-1.5 rounded text-muted-foreground hover:bg-surface-low hover:text-foreground transition-colors border-none bg-transparent cursor-pointer text-sm disabled:opacity-40 disabled:cursor-not-allowed";
  const toggleBtn = (active) =>
    `inline-flex items-center gap-2 px-3 py-2 rounded-md border text-sm cursor-pointer transition-colors ${
      active
        ? 'border-primary text-primary bg-primary/5'
        : 'border-border text-muted-foreground hover:border-primary hover:text-primary hover:bg-primary/5'
    }`;
  // `far` (regular) for the unchecked box: `fas fa-square` is a *solid* square,
  // which reads as an already-ticked control.
  const toggleIcon = (active) => (active ? 'fas fa-check-square' : 'far fa-square');

  return (
    <div className="bg-white border border-border rounded-lg mb-4 shadow-sm hover:shadow-card transition-shadow text-left">
      {/* Question header */}
      <div className="flex justify-between items-center px-4 py-3 border-b border-border bg-surface rounded-t-lg">
        <span className="font-semibold text-action bg-action/10 px-3 py-0.5 rounded-full text-sm">
          Q{question.order}
        </span>
        <div className="flex gap-1">
          <button type="button" className={iconBtn} onClick={handleMoveUp} disabled={isFirst} title={t('Move up')}>
            <i className="fas fa-chevron-up"></i>
          </button>
          <button type="button" className={iconBtn} onClick={handleMoveDown} disabled={isLast} title={t('Move down')}>
            <i className="fas fa-chevron-down"></i>
          </button>
          <button type="button" className={iconBtn} onClick={handleDuplicate} title={t('Duplicate')}>
            <i className="fas fa-copy"></i>
          </button>
          <button
            type="button"
            className={`${iconBtn} hover:text-error hover:bg-error-container`}
            onClick={handleDelete}
            title={t('Delete')}
          >
            <i className="fas fa-trash-alt"></i>
          </button>
        </div>
      </div>

      <div className="p-6">
        {/* Type row */}
        <div className="flex gap-4 items-center mb-6">
          <div className="flex-1 min-w-[250px]">
            <QuestionTypeSelector
              value={question.type}
              onChange={handleTypeChange}
              t={t}
              includeReviewTypes={includeReviewTypes}
              linkedFormId={linkedFormId}
              hasError={showErrors && !question.type}
            />
          </div>
          {!displayOnly && (
            <label className="flex items-center gap-2 cursor-pointer whitespace-nowrap select-none text-sm font-medium text-foreground">
              <input
                type="checkbox"
                checked={question.is_required}
                onChange={handleRequiredToggle}
                className="w-4 h-4 cursor-pointer accent-primary"
              />
              <span>{t('Required')}</span>
            </label>
          )}
        </div>

        {showErrors && !question.type && (
          <p className="text-error text-xs mb-4">{t('Choose a question type')}</p>
        )}

        {question.type && question.type !== 'information' && (
          <TranslatableFieldGroup
            label={t('Question Headline')}
            fieldName="headline"
            values={question.headline}
            languages={languages}
            onChange={(lang, value) => handleFieldChange('headline', lang, value)}
            required={true}
            autoTranslateEnabled={autoTranslateEnabled}
            showErrors={showErrors}
          />
        )}

        <TranslatableFieldGroup
          label={t('Description')}
          fieldName="description"
          values={question.description}
          languages={languages}
          onChange={(lang, value) => handleFieldChange('description', lang, value)}
          autoTranslateEnabled={autoTranslateEnabled}
          multiline={true}
        />

        {showPlaceholder && (
          <TranslatableFieldGroup
            label={t('Placeholder')}
            fieldName="placeholder"
            values={question.placeholder}
            languages={languages}
            onChange={(lang, value) => handleFieldChange('placeholder', lang, value)}
            autoTranslateEnabled={autoTranslateEnabled}
          />
        )}

        {showOptions && (
          <OptionsEditor
            options={question.options}
            languages={languages}
            onAdd={handleAddOption}
            onDelete={handleDeleteOption}
            onUpdateValue={handleUpdateOptionValue}
            onUpdateLabel={handleUpdateOptionLabel}
            t={t}
            autoTranslateEnabled={autoTranslateEnabled}
          />
        )}

        {showOptions && showErrors && (!question.options || question.options.length === 0) && (
          <p className="text-error text-xs mb-4">{t('Add at least one option')}</p>
        )}

        {showSettings && (
          <QuestionSettingsEditor
            type={question.type}
            settings={question.settings}
            onChange={handleSettingsChange}
            languages={languages}
            t={t}
            includeReviewTypes={includeReviewTypes}
          />
        )}

        {hasCountrySettings && (
          <CountryEditor
            settings={question.settings && question.settings.countryOptions}
            onChange={(countrySettings) => {
              dispatch({
                type: FORM_ACTIONS.SET_QUESTION_SETTINGS,
                sectionId,
                questionId: question.id,
                settings: { ...question.settings, countryOptions: countrySettings }
              });
            }}
            t={t}
          />
        )}

        {hasLinkedQuestion && (
          <LinkedQuestionSelector
            linkedFormId={linkedFormId}
            linkedQuestionId={question.linked_question_id}
            onChange={(questionId) =>
              dispatch({ type: FORM_ACTIONS.UPDATE_QUESTION_FIELD, sectionId, questionId: question.id, field: 'linked_question_id', value: questionId })
            }
            onQuestionDataLoad={(selectedQuestion) => {
              const currentHeadline = question.headline || {};
              const currentDescription = question.description || {};
              languages.forEach(lang => {
                const langCode = lang.code;
                if (!currentHeadline[langCode] && selectedQuestion.headline?.[langCode]) {
                  dispatch({ type: FORM_ACTIONS.UPDATE_QUESTION_FIELD, sectionId, questionId: question.id, field: 'headline', lang: langCode, value: selectedQuestion.headline[langCode] });
                }
                if (!currentDescription[langCode] && selectedQuestion.description?.[langCode]) {
                  dispatch({ type: FORM_ACTIONS.UPDATE_QUESTION_FIELD, sectionId, questionId: question.id, field: 'description', lang: langCode, value: selectedQuestion.description[langCode] });
                }
              });
            }}
            t={t}
          />
        )}

        {/* Toggle row */}
        <div className="flex gap-3 mt-4 pt-4 border-t border-border flex-wrap">
          {canHaveValidation && (
            <button type="button" className={toggleBtn(showValidation)} onClick={toggleValidation}>
              <i className={toggleIcon(showValidation)}></i>
              {t('Add Pattern Validation')}
            </button>
          )}
          <button type="button" className={toggleBtn(showDependency)} onClick={toggleDependency}>
            <i className={toggleIcon(showDependency)}></i>
            {t('Add Dependency')}
          </button>
          <button type="button" className={toggleBtn(showTagExpression)} onClick={toggleTagExpression}>
            <i className={toggleIcon(showTagExpression)}></i>
            {t('Add Tag Visibility')}
          </button>
          <button type="button" className={toggleBtn(showKey)} onClick={toggleKey}>
            <i className={toggleIcon(showKey)}></i>
            {t('Add Key')}
          </button>
        </div>

        {showKey && (
          <div className="mt-4 p-4 bg-surface rounded-md">
            <label className="block text-sm font-semibold text-foreground mb-1">
              {t('Key (for API/data identification)')}
            </label>
            <input
              type="text"
              value={question.key}
              onChange={(e) => handleFieldChange('key', null, e.target.value)}
              placeholder={t('e.g., email_address')}
              className="w-full px-3 py-2 border border-border rounded-md text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        )}

        {showDependency && (
          <DependencyEditor
            dependencyExpression={question.dependency_expression}
            onChange={handleDependencyChange}
            availableQuestions={allQuestions}
            currentQuestionId={question.id}
            currentSectionOrder={sectionOrder}
            currentQuestionOrder={question.order}
            linkedFormId={linkedFormId}
            t={t}
          />
        )}

        {showTagExpression && (
          <VisibilityExpressionEditor
            expression={question.tag_expression}
            onChange={handleTagExpressionChange}
            scope="question"
            eventId={eventId}
          />
        )}

        {showValidation && canHaveValidation && (
          <div className="mt-4 p-4 bg-warning-bg border border-warning/30 rounded-md">
            <h4 className="text-warning font-semibold text-sm mb-1">{t('Pattern Validation')}</h4>
            <p className="text-xs text-muted-foreground mb-3">
              {t('The answer must match this regular expression in full. For word limits use Length Settings above instead.')}
            </p>
            <TranslatableFieldGroup
              label={t('Validation Regex')}
              fieldName="validation_regex"
              values={question.validation_regex}
              languages={languages}
              onChange={(lang, value) => handleFieldChange('validation_regex', lang, value)}
              autoTranslateEnabled={false}
            />
            <TranslatableFieldGroup
              label={t('Validation Error Message')}
              fieldName="validation_text"
              values={question.validation_text}
              languages={languages}
              onChange={(lang, value) => handleFieldChange('validation_text', lang, value)}
              autoTranslateEnabled={autoTranslateEnabled}
            />
          </div>
        )}
      </div>
    </div>
  );
});

export default QuestionCard;
