import React, { useState, useEffect } from 'react';
import TranslatableFieldGroup from './TranslatableFieldGroup';
import QuestionTypeSelector from './QuestionTypeSelector';
import OptionsEditor from './OptionsEditor';
import QuestionSettingsEditor from './QuestionSettingsEditor';
import CountryEditor from './CountryEditor';
import DependencyEditor from './DependencyEditor';
import { FORM_ACTIONS } from '../actionTypes';
import './QuestionCard.css';

const QuestionCard = ({
  question,
  sectionId,
  sectionOrder,
  languages,
  dispatch,
  t,
  includeReviewTypes = false,
  allQuestions = []
}) => {
  const [showKey, setShowKey] = useState(!!question.key);
  const [showValidation, setShowValidation] = useState(
    !!question.validation_regex && Object.values(question.validation_regex).some(v => v)
  );
  const [showDependency, setShowDependency] = useState(!!question.dependency_expression);
  const [validationMode, setValidationMode] = useState('simple');
  const [wordLimitMin, setWordLimitMin] = useState({});
  const [wordLimitMax, setWordLimitMax] = useState({});

  // Parse existing regex to extract min/max if it's in simple word limit format
  useEffect(() => {
    if (!question.validation_regex) return;
    
    const newMin = {};
    const newMax = {};
    let hasSimplePattern = false;
    
    languages.forEach(lang => {
      const regex = question.validation_regex[lang.code];
      if (regex) {
        // Pattern: \b\w+\b with {min,max}, {min,}, or {0,max}
        const matchBoth = regex.match(/\{(\d+),(\d+)\}/);
        const matchMinOnly = regex.match(/\{(\d+),\}/);
        const matchMaxOnly = regex.match(/\{0,(\d+)\}/);
        
        if (matchBoth) {
          newMin[lang.code] = parseInt(matchBoth[1]);
          newMax[lang.code] = parseInt(matchBoth[2]);
          hasSimplePattern = true;
        } else if (matchMinOnly) {
          newMin[lang.code] = parseInt(matchMinOnly[1]);
          newMax[lang.code] = '';
          hasSimplePattern = true;
        } else if (matchMaxOnly) {
          newMin[lang.code] = '';
          newMax[lang.code] = parseInt(matchMaxOnly[1]);
          hasSimplePattern = true;
        }
      }
    });
    
    if (hasSimplePattern) {
      setValidationMode('simple');
      setWordLimitMin(newMin);
      setWordLimitMax(newMax);
    } else if (Object.values(question.validation_regex).some(v => v)) {
      setValidationMode('regex');
    }
  }, [languages, question.validation_regex]);

  const generateWordLimitRegex = (min, max) => {
    if (!min && !max) return '';
    if (min && max) return `^(\\b\\w+\\b[\\s]*){${min},${max}}$`;
    if (max) return `^(\\b\\w+\\b[\\s]*){0,${max}}$`;
    if (min) return `^(\\b\\w+\\b[\\s]*){${min},}$`;
    return '';
  };

  const getValidationText = (min, max) => {
    if (max && !min) {
      return t('You may enter no more than {{max}} words', { max });
    } else if (!max && min) {
      return t('You must enter at least {{min}} words', { min });
    } else if (max && min) {
      return t('You must enter between {{min}} and {{max}} words', { min, max });
    }
    return '';
  };

  const handleFieldChange = (field, lang, value) => {
    dispatch({
      type: FORM_ACTIONS.UPDATE_QUESTION_FIELD,
      sectionId,
      questionId: question.id,
      field,
      lang,
      value
    });
  };

  const handleValidationModeChange = (option) => {
    setValidationMode(option.value);
    
    if (option.value === 'simple') {
      // Clear regex and set word limit patterns
      languages.forEach(lang => {
        const min = wordLimitMin[lang.code] || '';
        const max = wordLimitMax[lang.code] || '';
        const regex = generateWordLimitRegex(min, max);
        const text = getValidationText(min, max);
        
        handleFieldChange('validation_regex', lang.code, regex);
        handleFieldChange('validation_text', lang.code, text);
      });
    }
  };

  const handleWordLimitChange = (lang, field, value) => {
    const numValue = value ? parseInt(value) : '';
    
    if (field === 'min') {
      setWordLimitMin({ ...wordLimitMin, [lang]: numValue });
      const max = wordLimitMax[lang] || '';
      const regex = generateWordLimitRegex(numValue, max);
      const text = getValidationText(numValue, max);
      handleFieldChange('validation_regex', lang, regex);
      handleFieldChange('validation_text', lang, text);
    } else {
      setWordLimitMax({ ...wordLimitMax, [lang]: numValue });
      const min = wordLimitMin[lang] || '';
      const regex = generateWordLimitRegex(min, numValue);
      const text = getValidationText(min, numValue);
      handleFieldChange('validation_regex', lang, regex);
      handleFieldChange('validation_text', lang, text);
    }
  };

  const handleTypeChange = (type) => {
    dispatch({
      type: FORM_ACTIONS.SET_QUESTION_TYPE,
      sectionId,
      questionId: question.id,
      questionType: type
    });
  };

  const handleRequiredToggle = () => {
    dispatch({
      type: FORM_ACTIONS.UPDATE_QUESTION_FIELD,
      sectionId,
      questionId: question.id,
      field: 'is_required',
      value: !question.is_required
    });
  };

  const handleSettingsChange = (settings) => {
    dispatch({
      type: FORM_ACTIONS.SET_QUESTION_SETTINGS,
      sectionId,
      questionId: question.id,
      settings
    });
  };

  const handleDependencyChange = (dependencyExpression) => {
    dispatch({
      type: FORM_ACTIONS.SET_QUESTION_DEPENDENCY,
      sectionId,
      questionId: question.id,
      dependencyExpression
    });
  };

  const handleAddOption = (optionData) => {
    dispatch({ 
      type: FORM_ACTIONS.ADD_OPTION, 
      sectionId, 
      questionId: question.id,
      optionData
    });
  };

  const handleDeleteOption = (optionId) => {
    dispatch({
      type: FORM_ACTIONS.DELETE_OPTION,
      sectionId,
      questionId: question.id,
      optionId
    });
  };

  const handleUpdateOptionValue = (optionId, value) => {
    dispatch({
      type: FORM_ACTIONS.UPDATE_OPTION,
      sectionId,
      questionId: question.id,
      optionId,
      field: 'value',
      value
    });
  };

  const handleUpdateOptionLabel = (optionId, lang, value) => {
    dispatch({
      type: FORM_ACTIONS.UPDATE_OPTION,
      sectionId,
      questionId: question.id,
      optionId,
      field: 'label',
      lang,
      value
    });
  };

  const handleDelete = () => {
    if (window.confirm(t('Are you sure you want to delete this question?'))) {
      dispatch({
        type: FORM_ACTIONS.DELETE_QUESTION,
        sectionId,
        questionId: question.id
      });
    }
  };

  const handleDuplicate = () => {
    dispatch({
      type: FORM_ACTIONS.DUPLICATE_QUESTION,
      sectionId,
      questionId: question.id
    });
  };

  const handleMoveUp = () => {
    dispatch({
      type: FORM_ACTIONS.MOVE_QUESTION,
      sectionId,
      questionId: question.id,
      direction: 'up'
    });
  };

  const handleMoveDown = () => {
    dispatch({
      type: FORM_ACTIONS.MOVE_QUESTION,
      sectionId,
      questionId: question.id,
      direction: 'down'
    });
  };

  const hasOptions = question.type && ['combobox', 'checkboxes', 'radio', 'single-choice'].includes(question.type);
  const hasPlaceholder = question.type && ['short-text', 'long-text', 'numeric', 'combobox', 'multi-file', 'country'].includes(question.type);
  const hasSettings = question.type && ['file', 'multi-file', 'numeric', 'reference', 'long-text', 'markdown'].includes(question.type);
  const hasCountrySettings = question.type === 'country';
  const canHaveValidation = question.type && ['short-text', 'long-text', 'markdown'].includes(question.type);

  return (
    <div className="question-card">
      <div className="question-header">
        <div className="question-order-badge">Q{question.order}</div>
        <div className="question-actions">
          <button
            type="button"
            className="question-action-btn"
            onClick={handleMoveUp}
            title={t('Move up')}
          >
            <i className="fas fa-chevron-up"></i>
          </button>
          <button
            type="button"
            className="question-action-btn"
            onClick={handleMoveDown}
            title={t('Move down')}
          >
            <i className="fas fa-chevron-down"></i>
          </button>
          <button
            type="button"
            className="question-action-btn"
            onClick={handleDuplicate}
            title={t('Duplicate')}
          >
            <i className="fas fa-copy"></i>
          </button>
          <button
            type="button"
            className="question-action-btn question-delete-btn"
            onClick={handleDelete}
            title={t('Delete')}
          >
            <i className="fas fa-trash-alt"></i>
          </button>
        </div>
      </div>

      <div className="question-body">
        <div className="question-type-row">
          <div className="question-type-selector-wrapper">
            <QuestionTypeSelector
              value={question.type}
              onChange={handleTypeChange}
              t={t}
              includeReviewTypes={includeReviewTypes}
            />
          </div>
          {question.type !== 'sub-heading' && question.type !== 'information' && (
            <label className="question-required-toggle">
              <input
                type="checkbox"
                checked={question.is_required}
                onChange={handleRequiredToggle}
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
          />
        )}

        <TranslatableFieldGroup
          label={t('Description')}
          fieldName="description"
          values={question.description}
          languages={languages}
          onChange={(lang, value) => handleFieldChange('description', lang, value)}
          multiline={true}
        />

        {hasPlaceholder && (
          <TranslatableFieldGroup
            label={t('Placeholder')}
            fieldName="placeholder"
            values={question.placeholder}
            languages={languages}
            onChange={(lang, value) => handleFieldChange('placeholder', lang, value)}
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
                settings: {
                  ...question.settings,
                  countryOptions: countrySettings
                }
              });
            }}
            t={t}
          />
        )}

        <div className="question-toggles">
          {canHaveValidation && (
            <button
              type="button"
              className={`question-toggle-btn ${showValidation ? 'active' : ''}`}
              onClick={() => setShowValidation(!showValidation)}
            >
              <i className={`fas ${showValidation ? 'fa-check-square' : 'fa-square'}`}></i>
              {t('Add Validation')}
            </button>
          )}
          <button
            type="button"
            className={`question-toggle-btn ${showDependency ? 'active' : ''}`}
            onClick={() => setShowDependency(!showDependency)}
          >
            <i className={`fas ${showDependency ? 'fa-check-square' : 'fa-square'}`}></i>
            {t('Add Dependency')}
          </button>
          <button
            type="button"
            className={`question-toggle-btn ${showKey ? 'active' : ''}`}
            onClick={() => setShowKey(!showKey)}
          >
            <i className={`fas ${showKey ? 'fa-check-square' : 'fa-square'}`}></i>
            {t('Add Key')}
          </button>
        </div>

        {showKey && (
          <div className="question-key-input">
            <label>{t('Key (for API/data identification)')}</label>
            <input
              type="text"
              value={question.key}
              onChange={(e) => handleFieldChange('key', null, e.target.value)}
              placeholder={t('e.g., email_address')}
              className="key-input"
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
            t={t}
          />
        )}

        {showValidation && canHaveValidation && (
          <div className="validation-section">
            <h4>{t('Validation')}</h4>
            
            <div className="validation-mode-toggle">
              <label className="radio-option">
                <input
                  type="radio"
                  name={`validation-mode-${question.id}`}
                  value="simple"
                  checked={validationMode === 'simple'}
                  onChange={() => handleValidationModeChange({ value: 'simple' })}
                />
                <span>{t('Word Limit')}</span>
              </label>
              <label className="radio-option">
                <input
                  type="radio"
                  name={`validation-mode-${question.id}`}
                  value="regex"
                  checked={validationMode === 'regex'}
                  onChange={() => handleValidationModeChange({ value: 'regex' })}
                />
                <span>{t('Regular Expression')}</span>
              </label>
            </div>

            {validationMode === 'simple' ? (
              <div className="word-limit-validation">
                {languages.map(lang => (
                  <div key={lang.code} className="word-limit-lang-group">
                    <label className="lang-label">{lang.description}</label>
                    <div className="word-limit-inputs">
                      <div className="word-limit-field">
                        <label>{t('Min Words')}</label>
                        <input
                          type="number"
                          min="0"
                          value={wordLimitMin[lang.code] || ''}
                          onChange={(e) => handleWordLimitChange(lang.code, 'min', e.target.value)}
                          placeholder="0"
                        />
                      </div>
                      <div className="word-limit-field">
                        <label>{t('Max Words')}</label>
                        <input
                          type="number"
                          min="0"
                          value={wordLimitMax[lang.code] || ''}
                          onChange={(e) => handleWordLimitChange(lang.code, 'max', e.target.value)}
                          placeholder="∞"
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
                />
                <TranslatableFieldGroup
                  label={t('Validation Error Message')}
                  fieldName="validation_text"
                  values={question.validation_text}
                  languages={languages}
                  onChange={(lang, value) => handleFieldChange('validation_text', lang, value)}
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
