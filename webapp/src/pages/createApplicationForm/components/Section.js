import React, { useState, useContext, useRef } from 'react';
import { Trans } from 'react-i18next';
import { ConfirmModal } from "react-bootstrap4-modal";
import Question from './Question';
import Context from '../../../context';
// import useIsMounted from './util';

const Section = ({
  t, sectionIndex, sections, inputs, lang
}) => {
  const { setAppFormData } = useContext(Context);
  const [isModelVisible, setIsModelVisible] = useState(false);
  const [input, setInput] = useState({
    name: inputs.name,
    description: inputs.description,
    order: Math.floor(Math.random() * 10) + 1,
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

  const handleOkDelete = () => {
    const updatedSections = sections.filter(s => s.id !== input.id);
    setAppFormData(updatedSections);
  }

  const handleConfirm = () => {
    setIsModelVisible(!isModelVisible);
  }

  const handleMoveUp = () => {
    const newOrder = input.order - 1;
    const newSections = sections.map(s => {
      if(s.id === input.id) {
        return {...input, order: newOrder}
      }
      if(s.order < input.order) {
        return {...s, order: input.order}
      }
      return s
    });
    setAppFormData(newSections);
  }

  const numSections = sections.length;
  const index = sectionIndex + 1;
  const isDisabled = sections.length === 1 ? true : false;

  return (
    <>
      <div
        className="section-wrapper"
        id={`section-${input.id}`}
        key={input.id}
        onBlur={!isModelVisible && updateSections}
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
            <div
              id="toggleTitle"
              className="title-desc-toggle"
              role="button"
              data-toggle="dropdown"
              aria-haspopup="true"
              aria-expanded="false"
            >
              <i className='fa fa-ellipsis-v fa-lg fa-dropdown'></i>
            </div>
            <div className="dropdown-menu" aria-labelledby="toggleTitle">
              <button
                className="dropdown-item delete-section"
                disabled={isDisabled}
                onClick={handleConfirm}
                >
                <i className="far fa-trash-alt fa-section"></i>
                {t("Delete Section")}
              </button>
              <button className="dropdown-item delete-section" >
                <i className="far fa-copy fa-section fa-duplicate"></i>
                {t("Duplicate Section")}
              </button>
              <button
                className="dropdown-item delete-section"
                onClick={handleMoveUp}
              >
                <i class="fas fa-angle-up fa-section fa-duplicate"></i>
                {t("Move Section Up")}
              </button>
              <button className="dropdown-item delete-section" >
              <i class="fas fa-angle-down fa-section fa-duplicate"></i>
                {t("Move Section Down")}
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
        {
          isModelVisible && (
            <ConfirmModal
              className='confirm-modal'
              visible={true}
              centered
              onOK={handleOkDelete}
              onCancel={() => handleConfirm()}
              okText={t("Yes - Delete")}
              cancelText={t("No - Don't delete")}>
              <p>
                {t("Are you sure you want to detele this section?")}
              </p>
            </ConfirmModal>
          )
        }
      </div>
    </>
  )
}

export default Section;
