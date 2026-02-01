import React, { useState } from 'react';
import TranslatableFieldGroup from './TranslatableFieldGroup';
import QuestionCard from './QuestionCard';
import DependencyEditor from './DependencyEditor';
import VisibilityExpressionEditor from './VisibilityExpressionEditor';
import { FORM_ACTIONS } from '../actionTypes';
import './SectionCard.css';

const SectionCard = ({
  section,
  sectionIndex,
  totalSections,
  languages,
  dispatch,
  t,
  includeReviewTypes = false,
  allQuestions = [],
  linkedFormId = null,
  autoTranslateEnabled = true
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [showKey, setShowKey] = useState(!!section.key);
  const [showDependency, setShowDependency] = useState(!!section.dependency_expression);
  const [showTagExpression, setShowTagExpression] = useState(!!section.tag_expression);

  const handleFieldChange = (field, lang, value) => {
    dispatch({
      type: FORM_ACTIONS.UPDATE_SECTION_FIELD,
      sectionId: section.id,
      field,
      lang,
      value
    });
  };

  const handleDependencyChange = (dependencyExpression) => {
    dispatch({
      type: FORM_ACTIONS.SET_SECTION_DEPENDENCY,
      sectionId: section.id,
      dependencyExpression
    });
  };

  const handleTagExpressionChange = (tagExpression) => {
    dispatch({
      type: FORM_ACTIONS.SET_SECTION_TAG_EXPRESSION,
      sectionId: section.id,
      tagExpression
    });
  };

  const handleDelete = () => {
    if (totalSections === 1) {
      alert(t('Cannot delete the only section. A form must have at least one section.'));
      return;
    }
    
    if (window.confirm(t('Are you sure you want to delete this section and all its questions?'))) {
      dispatch({
        type: FORM_ACTIONS.DELETE_SECTION,
        sectionId: section.id
      });
    }
  };

  const handleDuplicate = () => {
    dispatch({
      type: FORM_ACTIONS.DUPLICATE_SECTION,
      sectionId: section.id
    });
  };

  const handleMoveUp = () => {
    dispatch({
      type: FORM_ACTIONS.MOVE_SECTION,
      sectionId: section.id,
      direction: 'up'
    });
  };

  const handleMoveDown = () => {
    dispatch({
      type: FORM_ACTIONS.MOVE_SECTION,
      sectionId: section.id,
      direction: 'down'
    });
  };

  const handleAddQuestion = () => {
    dispatch({
      type: FORM_ACTIONS.ADD_QUESTION,
      sectionId: section.id
    });
  };

  const isFirst = sectionIndex === 0;
  const isLast = sectionIndex === totalSections - 1;

  return (
    <div className="section-card">
      <div className="section-header">
        <div className="section-header-left">
          <button
            type="button"
            className="section-expand-btn"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label={isExpanded ? t('Collapse section') : t('Expand section')}
          >
            <i className={`fas fa-chevron-${isExpanded ? 'down' : 'right'}`}></i>
          </button>
          <div className="section-title-badge">
            {t('Section {{number}} of {{total}}', { 
              number: section.order, 
              total: totalSections 
            })}
          </div>
        </div>
        
        <div className="section-actions">
          <button
            type="button"
            className="section-action-btn"
            onClick={handleMoveUp}
            disabled={isFirst}
            title={t('Move section up')}
          >
            <i className="fas fa-arrow-up"></i>
          </button>
          <button
            type="button"
            className="section-action-btn"
            onClick={handleMoveDown}
            disabled={isLast}
            title={t('Move section down')}
          >
            <i className="fas fa-arrow-down"></i>
          </button>
          <button
            type="button"
            className="section-action-btn"
            onClick={handleDuplicate}
            title={t('Duplicate section')}
          >
            <i className="fas fa-copy"></i>
          </button>
          <button
            type="button"
            className="section-action-btn section-delete-btn"
            onClick={handleDelete}
            disabled={totalSections === 1}
            title={t('Delete section')}
          >
            <i className="fas fa-trash-alt"></i>
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="section-body">
          <TranslatableFieldGroup
            label={t('Section Name')}
            fieldName="name"
            values={section.name}
            languages={languages}
            onChange={(lang, value) => handleFieldChange('name', lang, value)}
            required={true}
            autoTranslateEnabled={autoTranslateEnabled}
          />

          <TranslatableFieldGroup
            label={t('Section Description')}
            fieldName="description"
            values={section.description}
            languages={languages}
            onChange={(lang, value) => handleFieldChange('description', lang, value)}
            multiline={true}
            autoTranslateEnabled={autoTranslateEnabled}
          />

          <div className="section-toggles">
            <button
              type="button"
              className={`section-toggle-btn ${showDependency ? 'active' : ''}`}
              onClick={() => setShowDependency(!showDependency)}
            >
              <i className={`fas ${showDependency ? 'fa-check-square' : 'fa-square'}`}></i>
              {t('Add Dependency')}
            </button>
            <button
              type="button"
              className={`section-toggle-btn ${showTagExpression ? 'active' : ''}`}
              onClick={() => setShowTagExpression(!showTagExpression)}
            >
              <i className={`fas ${showTagExpression ? 'fa-check-square' : 'fa-square'}`}></i>
              {t('Add Tag Visibility')}
            </button>
            <button
              type="button"
              className={`section-toggle-btn ${showKey ? 'active' : ''}`}
              onClick={() => setShowKey(!showKey)}
            >
              <i className={`fas ${showKey ? 'fa-check-square' : 'fa-square'}`}></i>
              {t('Add Key')}
            </button>
          </div>

          {showDependency && (
            <DependencyEditor
              dependencyExpression={section.dependency_expression}
              onChange={handleDependencyChange}
              availableQuestions={allQuestions}
              currentSectionOrder={section.order}
              currentQuestionOrder={null}
              linkedFormId={linkedFormId}
              t={t}
            />
          )}

          {showTagExpression && (
            <VisibilityExpressionEditor
              expression={section.tag_expression}
              onChange={handleTagExpressionChange}
            />
          )}

          {showKey && (
            <div className="section-key-input">
              <label>{t('Section Key (for API/data identification)')}</label>
              <input
                type="text"
                value={section.key}
                onChange={(e) => handleFieldChange('key', null, e.target.value)}
                placeholder={t('e.g., personal_information')}
                className="key-input"
              />
            </div>
          )}

          <div className="questions-container">
            <h3 className="questions-heading">{t('Questions')}</h3>
            {section.questions.map((question) => (
              <QuestionCard
                key={question.id}
                question={question}
                sectionId={section.id}
                sectionOrder={section.order}
                languages={languages}
                dispatch={dispatch}
                t={t}
                includeReviewTypes={includeReviewTypes}
                allQuestions={allQuestions}
                linkedFormId={linkedFormId}
                autoTranslateEnabled={autoTranslateEnabled}
              />
            ))}
            
            <button
              type="button"
              className="add-question-btn"
              onClick={handleAddQuestion}
            >
              <i className="fas fa-plus"></i>
              {t('Add Question')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SectionCard;
