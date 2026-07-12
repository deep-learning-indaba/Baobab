import React, { useState } from 'react';
import TranslatableFieldGroup from './TranslatableFieldGroup';
import QuestionCard from './QuestionCard';
import DependencyEditor from './DependencyEditor';
import VisibilityExpressionEditor from './VisibilityExpressionEditor';
import { FORM_ACTIONS } from '../actionTypes';

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

  const handleFieldChange = (field, lang, value) =>
    dispatch({ type: FORM_ACTIONS.UPDATE_SECTION_FIELD, sectionId: section.id, field, lang, value });

  const handleDependencyChange = (dependencyExpression) =>
    dispatch({ type: FORM_ACTIONS.SET_SECTION_DEPENDENCY, sectionId: section.id, dependencyExpression });

  const handleTagExpressionChange = (tagExpression) =>
    dispatch({ type: FORM_ACTIONS.SET_SECTION_TAG_EXPRESSION, sectionId: section.id, tagExpression });

  const handleDelete = () => {
    if (totalSections === 1) {
      alert(t('Cannot delete the only section. A form must have at least one section.'));
      return;
    }
    if (window.confirm(t('Are you sure you want to delete this section and all its questions?'))) {
      dispatch({ type: FORM_ACTIONS.DELETE_SECTION, sectionId: section.id });
    }
  };

  const handleDuplicate = () =>
    dispatch({ type: FORM_ACTIONS.DUPLICATE_SECTION, sectionId: section.id });

  const handleMoveUp = () =>
    dispatch({ type: FORM_ACTIONS.MOVE_SECTION, sectionId: section.id, direction: 'up' });

  const handleMoveDown = () =>
    dispatch({ type: FORM_ACTIONS.MOVE_SECTION, sectionId: section.id, direction: 'down' });

  const handleAddQuestion = () =>
    dispatch({ type: FORM_ACTIONS.ADD_QUESTION, sectionId: section.id });

  const isFirst = sectionIndex === 0;
  const isLast = sectionIndex === totalSections - 1;

  const iconBtn = "p-2 rounded-md bg-white border border-border text-muted-foreground hover:bg-surface-low hover:text-foreground transition-colors disabled:opacity-40 disabled:cursor-not-allowed text-sm";
  const toggleBtn = (active) =>
    `inline-flex items-center gap-2 px-3 py-2 rounded-md border text-sm cursor-pointer transition-colors ${
      active
        ? 'border-primary text-primary bg-primary/5'
        : 'border-border text-muted-foreground hover:border-primary hover:text-primary hover:bg-primary/5'
    }`;

  return (
    <div className="bg-white border-2 border-border rounded-xl mb-8 shadow-sm">
      {/* Section header */}
      <div className="flex justify-between items-center px-6 py-4 bg-gradient-to-r from-surface to-surface-low border-b border-border rounded-t-xl">
        <div className="flex items-center gap-4">
          <button
            type="button"
            className="p-2 text-muted-foreground hover:text-foreground transition-colors cursor-pointer border-none bg-transparent"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label={isExpanded ? t('Collapse section') : t('Expand section')}
          >
            <i className={`fas fa-chevron-${isExpanded ? 'down' : 'right'}`}></i>
          </button>
          <span className="font-semibold text-foreground text-base">
            {t('Section {{number}} of {{total}}', { number: section.order, total: totalSections })}
          </span>
        </div>

        <div className="flex gap-2">
          <button type="button" className={iconBtn} onClick={handleMoveUp} disabled={isFirst} title={t('Move section up')}>
            <i className="fas fa-arrow-up"></i>
          </button>
          <button type="button" className={iconBtn} onClick={handleMoveDown} disabled={isLast} title={t('Move section down')}>
            <i className="fas fa-arrow-down"></i>
          </button>
          <button type="button" className={iconBtn} onClick={handleDuplicate} title={t('Duplicate section')}>
            <i className="fas fa-copy"></i>
          </button>
          <button
            type="button"
            className={`${iconBtn} hover:border-error hover:text-error hover:bg-error-container`}
            onClick={handleDelete}
            disabled={totalSections === 1}
            title={t('Delete section')}
          >
            <i className="fas fa-trash-alt"></i>
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="p-8">
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

          {/* Toggle row */}
          <div className="flex gap-3 mt-4 pt-4 border-t border-border flex-wrap">
            <button type="button" className={toggleBtn(showDependency)} onClick={() => setShowDependency(!showDependency)}>
              <i className={`fas ${showDependency ? 'fa-check-square' : 'fa-square'}`}></i>
              {t('Add Dependency')}
            </button>
            <button type="button" className={toggleBtn(showTagExpression)} onClick={() => setShowTagExpression(!showTagExpression)}>
              <i className={`fas ${showTagExpression ? 'fa-check-square' : 'fa-square'}`}></i>
              {t('Add Tag Visibility')}
            </button>
            <button type="button" className={toggleBtn(showKey)} onClick={() => setShowKey(!showKey)}>
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
            <div className="mt-4 p-4 bg-surface rounded-md">
              <label className="block text-sm font-semibold text-foreground mb-1">
                {t('Section Key (for API/data identification)')}
              </label>
              <input
                type="text"
                value={section.key}
                onChange={(e) => handleFieldChange('key', null, e.target.value)}
                placeholder={t('e.g., personal_information')}
                className="w-full px-3 py-2 border border-border rounded-md text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          )}

          {/* Questions */}
          <div className="mt-8">
            <h3 className="text-base font-semibold text-foreground mb-4 pb-2 border-b-2 border-border">
              {t('Questions')}
            </h3>
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
              onClick={handleAddQuestion}
              className="w-full py-4 bg-white border-2 border-dashed border-border rounded-lg cursor-pointer text-primary font-medium hover:bg-surface-low hover:border-primary transition-colors flex items-center justify-center gap-2"
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
