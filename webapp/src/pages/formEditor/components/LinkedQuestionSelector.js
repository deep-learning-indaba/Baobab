import React, { useState, useEffect } from 'react';
import { formServices } from '../../../services/form/form.service';
import './LinkedQuestionSelector.css';

const LinkedQuestionSelector = ({ linkedFormId, linkedQuestionId, onChange, t }) => {
  const [linkedFormQuestions, setLinkedFormQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!linkedFormId) {
      setLinkedFormQuestions([]);
      return;
    }

    const fetchLinkedFormQuestions = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await formServices.getForm(linkedFormId);
        if (response.form && response.form.sections) {
          const allQuestions = [];
          response.form.sections.forEach((section, sectionIdx) => {
            const sectionName = typeof section.name === 'object' 
              ? (section.name.en || Object.values(section.name)[0]) 
              : section.name;
            
            section.questions.forEach((question) => {
              const questionHeadline = typeof question.headline === 'object'
                ? (question.headline.en || Object.values(question.headline)[0])
                : question.headline;
              
              allQuestions.push({
                id: question.id,
                label: `${sectionName} - ${questionHeadline || `Question ${question.order}`}`,
                type: question.type
              });
            });
          });
          setLinkedFormQuestions(allQuestions);
        }
      } catch (err) {
        console.error('Error fetching linked form questions:', err);
        setError(t('Failed to load questions from linked form'));
      } finally {
        setLoading(false);
      }
    };

    fetchLinkedFormQuestions();
  }, [linkedFormId, t]);

  if (!linkedFormId) {
    return (
      <div className="linked-question-selector-info">
        <i className="fas fa-info-circle"></i>
        <span>{t('Please set a linked form in Form Settings first')}</span>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="linked-question-selector-loading">
        <i className="fas fa-spinner fa-spin"></i>
        <span>{t('Loading questions from linked form...')}</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="linked-question-selector-error">
        <i className="fas fa-exclamation-triangle"></i>
        <span>{error}</span>
      </div>
    );
  }

  return (
    <div className="linked-question-selector">
      <label>{t('Select Question from Linked Form')}</label>
      <select
        value={linkedQuestionId || ''}
        onChange={(e) => onChange(e.target.value ? parseInt(e.target.value) : null)}
        className="linked-question-select"
      >
        <option value="">{t('Select a question...')}</option>
        {linkedFormQuestions.map((q) => (
          <option key={q.id} value={q.id}>
            {q.label} ({q.type})
          </option>
        ))}
      </select>
      <span className="linked-question-hint">
        {t('This will display the user\'s answer to the selected question from the linked form')}
      </span>
    </div>
  );
};

export default LinkedQuestionSelector;
