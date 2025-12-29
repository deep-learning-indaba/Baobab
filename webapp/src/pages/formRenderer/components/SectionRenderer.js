import React from 'react';
import QuestionRenderer from './QuestionRenderer';
import MarkdownRenderer from '../../../components/MarkdownRenderer';
import './SectionRenderer.css';

const SectionRenderer = ({
  section,
  answers,
  answersDict,
  onAnswerChange,
  validationErrors,
  language,
  isQuestionVisible,
  disabled = false,
  t
}) => {
  // Get translated content
  const getTranslatedField = (field) => {
    if (!section[field]) return null;
    if (typeof section[field] === 'object') {
      return section[field][language] || section[field]['en'] || Object.values(section[field])[0];
    }
    return section[field];
  };

  const name = getTranslatedField('name');
  const description = getTranslatedField('description');

  // Filter visible questions
  const visibleQuestions = section.questions
    ? section.questions
        .filter(q => q.is_active !== false)
        .filter(q => isQuestionVisible(q, section))
        .sort((a, b) => a.order - b.order)
    : [];

  if (visibleQuestions.length === 0) {
    return null;
  }

  return (
    <div className="section-renderer">
      <div className="section-header">
        {name && <h2 className="section-name">{name}</h2>}
      </div>

      {description && (
        <div className="section-description">
          <MarkdownRenderer source={description} />
        </div>
      )}

      <div className="section-questions">
        {visibleQuestions.map(question => (
          <QuestionRenderer
            key={question.id}
            question={question}
            value={answersDict[question.id]}
            onChange={onAnswerChange}
            language={language}
            validationError={validationErrors[question.id]}
            disabled={disabled}
            t={t}
          />
        ))}
      </div>
    </div>
  );
};

export default SectionRenderer;
