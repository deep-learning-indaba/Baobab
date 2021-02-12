import React, { useState, useContext } from 'react';
import { Trans } from 'react-i18next';
import Question from './Question';
import Context from '../../../context';

const Section = ({
  t, sectionIndex, sections, inputs, lang
}) => {
  const { setAppFormData } = useContext(Context);

  const [input, setInput] = useState({
    name: inputs.name,
    description: inputs.description,
    id: inputs.id,
    questions: inputs.questions
  });

  const handleChange = (prop) => (e) => {
    const target = input[prop];
    setInput({...input, [prop]: {...target, [lang]: e.target.value}});
  }

  const updateSections = () => { // Update sections in the application form when section loses focus
    const updatedSections = sections.map(s => {
      if(s.id === input.id) return input;
      return s;
    })
    setAppFormData([...updatedSections]);
  }

  const addQuestion = () => {
    const qsts = input.questions;
    setInput({...input, questions: [...qsts, {
      id: `${Math.random()}`,
      order: qsts.length && qsts.length + 1,
      headline: {
        en: '',
        fr: ''
      },
      placeholder: {
        en: '',
        fr: ''
      },
      type: null,
      options: {
        en: [],
        fr: []
      },
      value: {
        en: '',
        fr: ''
      },
      label: {
        en: '',
        fr: ''
      },
      required: false
    }]});
  }

  const handleQuestions = (inpt) => {
    setInput({...input, questions: inpt});
  }

  const numSections = sections.length;
  const index = sectionIndex + 1;

  return (
    <>
      <div
        className="section-wrapper"
        id={`section-${input.id}`}
        key={input.id}
        onBlur={updateSections}
      >
        <div className="section-number">
          <Trans i18nKey='sectionPlace' >Section {{index}} of {{numSections}}</Trans>
        </div>
        <div className="title-description">
          <div className="section-header">
            <input
              type="text"
              value={input.name[lang]}
              onChange={handleChange('name')}
              className="section-inputs section-title"
            />
            <button
              className="title-desc-toggle"
              name="title-desc-toggle"
              data-toggle="dropdown"
              aria-haspopup="true"
              aria-expanded="false"
            >
              <i className='fa fa-ellipsis-v fa-lg fa-dropdown'></i>
            </button>
            <div className="dropdown-menu" aria-labelledby="title-desc-toggle">
              <button className="delete-section">
                {t("Delete Section")}
              </button>
              <button className="delete-section">
                {t("Duplicate Section")}
              </button>
            </div>
          </div>
          <input
            name="section-desc"
            type="text"
            value={input.description[lang]}
            placeholder={t('Description')}
            onChange={handleChange('description')}
            className="section-inputs section-desc"
           /> 
        </div>

        {input.questions.map(question => (
          <Question
            inputs={question}
            key={question.id}
            t={t}
            num={question.id}
            questions={input.questions}
            setQuestions={handleQuestions}
            setSection={setInput}
            sections={sections}
            sectionId={input.id}
            section={input}
            lang={lang}
            />
        ))}
        <div className='add-question-wrapper'>
          <button
            className="add-question-btn"
            data-title={t('Add Question')}
            onMouseUp={() => addQuestion()}
          >
            <i class="fas fa-plus add-section-icon"></i>
          </button>
        </div>
      </div>
    </>
  )
}

export default Section;