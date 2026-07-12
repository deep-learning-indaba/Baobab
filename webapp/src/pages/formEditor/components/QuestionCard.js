import React, { useState, useEffect } from 'react';
import TranslatableFieldGroup from './TranslatableFieldGroup';
import QuestionTypeSelector from './QuestionTypeSelector';
import OptionsEditor from './OptionsEditor';
import QuestionSettingsEditor from './QuestionSettingsEditor';
import CountryEditor from './CountryEditor';
import DependencyEditor from './DependencyEditor';
import LinkedQuestionSelector from './LinkedQuestionSelector';
import { FORM_ACTIONS } from '../actionTypes';

const QuestionCard = ({
  question,
  sectionId,
  sectionOrder,
  languages,
  dispatch,
  t,
  includeReviewTypes = false,
  allQuestions = [],
  linkedFormId = null,
  autoTranslateEnabled = true
}) => {
  const [showKey, setShowKey] = useState(!!question.key);
  const [showValidation, setShowValidation] = useState(
    !!question.validation_regex && Object.values(question.validation_regex).some(v => v)
  );
  const [showDependency, setShowDependency] = useState(!!question.dependency_expression);
  const [validationMode, setValidationMode] = useState('simple');
  const [wordLimitMin, setWordLimitMin] = useState({});
  const [wordLimitMax, setWordLimitMax] = useState({});

  useEffect(() => {
    if (!question.validation_regex) return;
    const newMin = {};
    const newMax = {};
    let hasSimplePattern = false;
    languages.forEach(lang => {
      const regex = question.validation_regex[lang.code];
      if (regex) {
        const matchBoth = regex.match(/\{(\d+),(\d+)\}/);
        const matchMinOnly = regex.match(/\{(\d+),\}/);
        const matchMaxOnly = regex.match(/\{0,(\d+)\}/);
        if (matchBoth) { newMin[lang.code] = parseInt(matchBoth[1]); newMax[lang.code] = parseInt(matchBoth[2]); hasSimplePattern = true; }
        else if (matchMinOnly) { newMin[lang.code] = parseInt(matchMinOnly[1]); newMax[lang.code] = ''; hasSimplePattern = true; }
        else if (matchMaxOnly) { newMin[lang.code] = ''; newMax[lang.code] = parseInt(matchMaxOnly[1]); hasSimplePattern = true; }
      }
    });
    if (hasSimplePattern) { setValidationMode('simple'); setWordLimitMin(newMin); setWordLimitMax(newMax); }
    else if (Object.values(question.validation_regex).some(v => v)) { setValidationMode('regex'); }
  }, [languages, question.validation_regex]);

  const generateWordLimitRegex = (min, max) => {
    if (!min && !max) return '';
    if (min && max) return `^(\\b\\w+\\b[\\s]*){${min},${max}}$`;
    if (max) return `^(\\b\\w+\\b[\\s]*){0,${max}}$`;
    if (min) return `^(\\b\\w+\\b[\\s]*){${min},}$`;
    return '';
  };

  const getValidationText = (min, max) => {
    if (max && !min) return t('You may enter no more than {{max}} words', { max });
    if (!max && min) return t('You must enter at least {{min}} words', { min });
    if (max && min) return t('You must enter between {{min}} and {{max}} words', { min, max });
    return '';
  };

  const handleFieldChange = (field, lang, value) =>
    dispatch({ type: FORM_ACTIONS.UPDATE_QUESTION_FIELD, sectionId, questionId: question.id, field, lang, value });

  const handleValidationModeChange = (option) => {
    setValidationMode(option.value);
    if (option.value === 'simple') {
      languages.forEach(lang => {
        const min = wordLimitMin[lang.code] || '';
        const max = wordLimitMax[lang.code] || '';
        handleFieldChange('validation_regex', lang.code, generateWordLimitRegex(min, max));
        handleFieldChange('validation_text', lang.code, getValidationText(min, max));
      });
    }
  };

  const handleWordLimitChange = (lang, field, value) => {
    const numValue = value ? parseInt(value) : '';
    if (field === 'min') {
      setWordLimitMin({ ...wordLimitMin, [lang]: numValue });
      const max = wordLimitMax[lang] || '';
      handleFieldChange('validation_regex', lang, generateWordLimitRegex(numValue, max));
      handleFieldChange('validation_text', lang, getValidationText(numValue, max));
    } else {
      setWordLimitMax({ ...wordLimitMax, [lang]: numValue });
      const min = wordLimitMin[lang] || '';
      handleFieldChange('validation_regex', lang, generateWordLimitRegex(min, numValue));
      handleFieldChange('validation_text', lang, getValidationText(min, numValue));
    }
  };

  const handleTypeChange = (type) =>
    dispatch({ type: FORM_ACTIONS.SET_QUESTION_TYPE, sectionId, questionId: question.id, questionType: type });

  const handleRequiredToggle = () =>
    dispatch({ type: FORM_ACTIONS.UPDATE_QUESTION_FIELD, sectionId, questionId: question.id, field: 'is_required', value: !question.is_required });

  const handleSettingsChange = (settings) =>
    dispatch({ type: FORM_ACTIONS.SET_QUESTION_SETTINGS, sectionId, questionId: question.id, settings });

  const handleDependencyChange = (dependencyExpression) =>
    dispatch({ type: FORM_ACTIONS.SET_QUESTION_DEPENDENCY, sectionId, questionId: question.id, dependencyExpression });

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

  const hasOptions = question.type && ['combobox', 'checkboxes', 'radio', 'single-choice'].includes(question.type);
  const hasPlaceholder = question.type && ['short-text', 'long-text', 'numeric', 'combobox', 'multi-file', 'country'].includes(question.type);
  const hasSettings = question.type && ['file', 'multi-file', 'numeric', 'reference', 'long-text', 'markdown'].includes(question.type);
  const hasCountrySettings = question.type === 'country';
  const hasLinkedQuestion = question.type === 'linked-form-question';
  const canHaveValidation = question.type && ['short-text', 'long-text', 'markdown'].includes(question.type);

  const iconBtn = "p-1.5 rounded text-muted-foreground hover:bg-surface-low hover:text-foreground transition-colors border-none bg-transparent cursor-pointer text-sm";
  const toggleBtn = (active) =>
    `inline-flex items-center gap-2 px-3 py-2 rounded-md border text-sm cursor-pointer transition-colors ${
      active
        ? 'border-primary text-primary bg-primary/5'
        : 'border-border text-muted-foreground hover:border-primary hover:text-primary hover:bg-primary/5'
    }`;

  return (
    <div className="bg-white border border-border rounded-lg mb-4 shadow-sm hover:shadow-card transition-shadow">
      {/* Question header */}
      <div className="flex justify-between items-center px-4 py-3 border-b border-border bg-surface rounded-t-lg">
        <span className="font-semibold text-action bg-action/10 px-3 py-0.5 rounded-full text-sm">
          Q{question.order}
        </span>
        <div className="flex gap-1">
          <button type="button" className={iconBtn} onClick={handleMoveUp} title={t('Move up')}>
            <i className="fas fa-chevron-up"></i>
          </button>
          <button type="button" className={iconBtn} onClick={handleMoveDown} title={t('Move down')}>
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
            />
          </div>
          {question.type !== 'sub-heading' && question.type !== 'information' && (
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

        {question.type && question.type !== 'information' && (
          <TranslatableFieldGroup
            label={t('Question Headline')}
            fieldName="headline"
            values={question.headline}
            languages={languages}
            onChange={(lang, value) => handleFieldChange('headline', lang, value)}
            required={true}
            autoTranslateEnabled={autoTranslateEnabled}
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

        {hasPlaceholder && (
          <TranslatableFieldGroup
            label={t('Placeholder')}
            fieldName="placeholder"
            values={question.placeholder}
            languages={languages}
            onChange={(lang, value) => handleFieldChange('placeholder', lang, value)}
            autoTranslateEnabled={autoTranslateEnabled}
          />
        )}

        {hasOptions && (
          <OptionsEditor
            options={question.options}
            languages={languages}
            onAdd={handleAddOption}
            onDelete={handleDeleteOption}
            onUpdateValue={handleUpdateOptionValue}
            onUpdateLabel={handleUpdateOptionLabel}
            t={t}
          />
        )}

        {hasSettings && (
          <QuestionSettingsEditor
            type={question.type}
            settings={question.settings}
            onChange={handleSettingsChange}
            languages={languages}
            t={t}
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
            <button type="button" className={toggleBtn(showValidation)} onClick={() => setShowValidation(!showValidation)}>
              <i className={`fas ${showValidation ? 'fa-check-square' : 'fa-square'}`}></i>
              {t('Add Validation')}
            </button>
          )}
          <button type="button" className={toggleBtn(showDependency)} onClick={() => setShowDependency(!showDependency)}>
            <i className={`fas ${showDependency ? 'fa-check-square' : 'fa-square'}`}></i>
            {t('Add Dependency')}
          </button>
          <button type="button" className={toggleBtn(showKey)} onClick={() => setShowKey(!showKey)}>
            <i className={`fas ${showKey ? 'fa-check-square' : 'fa-square'}`}></i>
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

        {showValidation && canHaveValidation && (
          <div className="mt-4 p-4 bg-warning-bg border border-warning/30 rounded-md">
            <h4 className="text-warning font-semibold text-sm mb-3">{t('Validation')}</h4>

            {/* Segmented control */}
            <div className="inline-flex bg-surface-mid rounded-lg p-1 gap-0 mb-4">
              {[
                { value: 'simple', label: t('Word Limit') },
                { value: 'regex', label: t('Regular Expression') }
              ].map(opt => (
                <label key={opt.value} className="relative cursor-pointer">
                  <input
                    type="radio"
                    name={`validation-mode-${question.id}`}
                    value={opt.value}
                    checked={validationMode === opt.value}
                    onChange={() => handleValidationModeChange({ value: opt.value })}
                    className="sr-only peer"
                  />
                  <span className="block px-4 py-1.5 text-sm font-medium text-muted-foreground rounded-md transition-all peer-checked:bg-white peer-checked:text-foreground peer-checked:shadow-sm">
                    {opt.label}
                  </span>
                </label>
              ))}
            </div>

            {validationMode === 'simple' ? (
              <div className="flex flex-col gap-3">
                {languages.map(lang => (
                  <div key={lang.code} className="p-3 border border-border rounded-md bg-white">
                    <label className="block font-semibold text-foreground text-sm mb-2">{lang.description}</label>
                    <div className="flex gap-4">
                      <div className="flex-1">
                        <label className="block text-xs text-muted-foreground mb-1">{t('Min Words')}</label>
                        <input
                          type="number"
                          min="0"
                          value={wordLimitMin[lang.code] || ''}
                          onChange={(e) => handleWordLimitChange(lang.code, 'min', e.target.value)}
                          placeholder="0"
                          className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                        />
                      </div>
                      <div className="flex-1">
                        <label className="block text-xs text-muted-foreground mb-1">{t('Max Words')}</label>
                        <input
                          type="number"
                          min="0"
                          value={wordLimitMax[lang.code] || ''}
                          onChange={(e) => handleWordLimitChange(lang.code, 'max', e.target.value)}
                          placeholder="∞"
                          className="w-full px-3 py-2 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <>
                <TranslatableFieldGroup
                  label={t('Validation Regex')}
                  fieldName="validation_regex"
                  values={question.validation_regex}
                  languages={languages}
                  onChange={(lang, value) => handleFieldChange('validation_regex', lang, value)}
                  autoTranslateEnabled={autoTranslateEnabled}
                />
                <TranslatableFieldGroup
                  label={t('Validation Error Message')}
                  fieldName="validation_text"
                  values={question.validation_text}
                  languages={languages}
                  onChange={(lang, value) => handleFieldChange('validation_text', lang, value)}
                  autoTranslateEnabled={autoTranslateEnabled}
                />
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default QuestionCard;
