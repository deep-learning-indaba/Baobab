import React, { useState } from 'react';
import Question from './Question';

const Section = ({
  t, num, setSection, sections, inputs,
  addSection, addQuestion
}) => {
  const [input, setInput] = useState({
    name: inputs ? inputs.name : 'Undefined',
    description: inputs ? inputs.description : '',
    id: inputs.id,
    questions: inputs.questions
  });

  const handleChange = (prop) => (e) => {
    setInput({...input, [prop]: e.target.value});
  }
  const updateSections = () => { // Update sections in the application form when section loses focus
    sections[num-1] = input;
    setSection([...sections]);
  }
  const handleQuestions = (inpt) => {
    setInput({...input, questions: inpt})
  }
  // const addQuestion = () => {
  //   const q = [...input.questions, {
  //     id: `${Math.random()}`,
  //     order: input.questions.length && input.questions.length + 1,
  //     headline: 'Untitled Question',
  //     placeholder: '',
  //     type: null,
  //     options: [],
  //     value: '',
  //     label: '',
  //     required: false
  //   }];
  //   setInput({...input, questions: q})
  // } 
  return (
    <>
      <div
        className="section-wrapper"
        // onBlur={updateSections}
      >
        <div className="section-number">
          <label>{t('Section') + ` ${num} ` + t('of') + ` ${sections.length}`  }</label>
        </div>
        <div className="title-description">
          <div className="section-header">
            <input
              type="text"
              value={input.name}
              onChange={handleChange('name')}
              className="section-inputs section-title"
              onBlur={updateSections}
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
              <button
                className="delete-section"
                onClick={() => addSection()}
              >
                {t("Add Section")}
              </button>
              <button className="delete-section">
                {t("Delete Section")}
              </button>
              <button className="delete-section">
                {t("Duplicate Section")}
              </button>
              <button
                className="delete-section"
                onClick={() => addQuestion(inputs.id)}
              >
                {t("Add Question")}
              </button>
            </div>
          </div>
          <input
            name="section-desc"
            type="text"
            value={input.description}
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
            setSection={setSection}
            sections={sections}
            />
        ))}
      </div>
    </>
  )
}

export default Section;