import React from 'react';
import QuestionRenderer from './QuestionRenderer';
import MarkdownRenderer from '../../../components/MarkdownRenderer';

const SectionRenderer = ({
  section,
  answers,
  answersDict,
  onAnswerChange,
  validationErrors,
  language,
  isQuestionVisible,
  disabled = false,
  linkedResponse,
  t
}) => {
  const getTranslatedField = (field) => {
    if (!section[field]) return null;
    if (typeof section[field] === 'object') {
      return section[field][language] || section[field]['en'] || Object.values(section[field])[0];
    }
    return section[field];
  };

  const name = getTranslatedField('name');
  const description = getTranslatedField('description');

  const visibleQuestions = section.questions
    ? section.questions
        .filter(q => q.is_active !== false)
        .filter(q => isQuestionVisible(q, section))
        .sort((a, b) => a.order - b.order)
    : [];

  if (visibleQuestions.length === 0) return null;

  return (
    <div className="bg-white border border-border rounded-lg p-8 md:p-4 shadow-sm text-left">
      <div className="flex flex-col items-start mb-8 pb-4 border-b-2 border-border">
        {name && <h2 className="text-2xl md:text-xl font-semibold text-foreground mb-0">{name}</h2>}
      </div>

      {description && (
        <div className="text-muted-foreground text-base leading-relaxed w-full mb-8">
          <MarkdownRenderer source={description} />
        </div>
      )}

      <div className="flex flex-col gap-6">
        {visibleQuestions.map(question => (
          <QuestionRenderer
            key={question.id}
            question={question}
            value={answersDict[question.id]}
            onChange={onAnswerChange}
            language={language}
            validationError={validationErrors[question.id]}
            disabled={disabled}
            linkedResponse={linkedResponse}
            t={t}
          />
        ))}
      </div>
    </div>
  );
};

export default SectionRenderer;
