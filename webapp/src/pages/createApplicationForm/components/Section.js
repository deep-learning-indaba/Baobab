import React,
{
  useState, forwardRef, createRef
} from 'react';
import { Trans } from 'react-i18next';
import Question from './Question';
import {
  Modal, AnimateSections, handleMove,
  drag, drop
} from './util';

const Section = forwardRef(({
  t, sectionIndex, sections, inputs, lang,
  setSection, handleDrag, handleDrop,
  setApplytransition
}, ref) => {
  const [isModelVisible, setIsModelVisible] = useState(false);
  const [parentDropable, setParentDropable] = useState(true)

  const [input, setInput] = useState({
    name: inputs.name,
    description: inputs.description,
    order: inputs.order,
    id: inputs.id,
    questions: inputs.questions
  });
  const [questionAnimation, setQuestionAnimation] = useState(false);
  const [dragId, setDragId] = useState();

  const handleChange = (prop) => (e) => {
    const target = input[prop];
    setInput({...input, [prop]: {...target, [lang]: e.target.value}});
  }

  const updateSections = () => { // Update sections in the application form when section loses focus
    const updatedSections = sections.map(s => {
      if(s.id === input.id) return input;
      return s;
    });
    setSection([...updatedSections]);
    setQuestionAnimation(false);
    setApplytransition(false);
  }

  const addQuestion = () => {
    const qsts = input.questions;
    const qst = {
      id: `${Math.random()}`,
      order: qsts.length + 1,
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
    }
    const updatedSections = sections.map(s => {
      if (s.id === input.id) {
        s = {...input, questions: [...qsts, qst]};
      }
      return s;
    });
    setInput({...input, questions: [...qsts, qst]});
    setApplytransition(false);
    setQuestionAnimation(false);
  }

  const handleQuestions = (inpt) => {
    setInput({...input, questions: inpt});
  }

  const handleOkDelete = () => {
    const updatedSections = sections.filter(s => s.id !== input.id);
    setSection(updatedSections);
  }

  const handleConfirm = () => {
    setIsModelVisible(!isModelVisible);
  }

  const handleMoveSUp = () => {
    handleMove({
      elements: sections,
      index: sectionIndex,
      setState: setSection,
      u: true
    });
  }

  const handleMoveSDown = () => {
    handleMove({
      elements: sections,
      index: sectionIndex,
      setState: setSection
    });
  }

  const handleDragQ = (e) => {
    drag(e, setDragId);
  }

  const handleDropQ = (e) => {
    drop({
      event: e,
      elements: input.questions,
      dragId,
      setState: setInput,
      section: input,
      setAnimation: setQuestionAnimation,
      setSection: setSection,
      sections
    });
    setParentDropable(false);
    setApplytransition(false);
  }

  const handleMouseDown = () => {
    setParentDropable(true);
  }

  const handleMouseOut = () => {
    setParentDropable(false);
  }

  const numSections = sections.length;
  const index = sectionIndex + 1;
  const isDisabled = sections.length === 1 ? true : false;

  return (
    <div
      className="section-wrapper"
      id={input.id}
      key={input.id}
      onBlur={!isModelVisible && updateSections}
      ref={ref}
      draggable={parentDropable}
      onDragOver={e => e.preventDefault()}
      onDragStart={handleDrag}
      onDrop={handleDrop}
    >
      <div
        className="section-number"
        onMouseDown={handleMouseDown}
        onMouseOut={handleMouseOut}
      >
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
              onClick={handleMoveSUp}
              disabled={index === 1}
            >
              <i class="fas fa-angle-up fa-section fa-duplicate"></i>
              {t("Move Section Up")}
            </button>
            <button
              disabled={index === sections.length}
              className="dropdown-item delete-section"
              onClick={handleMoveSDown}
            >
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
      <AnimateSections
        applyTransition={questionAnimation}
        setApplytransition={setQuestionAnimation}
      >
        {input.questions.map((question, i) => (
          <Question
            inputs={question}
            key={question.id}
            t={t}
            ref={createRef()}
            num={question.id}
            questions={input.questions}
            setQuestions={handleQuestions}
            setSection={setInput}
            setSections={setSection}
            sections={sections}
            sectionId={input.id}
            section={input}
            lang={lang}
            setApplytransition={setApplytransition}
            questionIndex={i}
            setQuestionAnimation={setQuestionAnimation}
            handleDrag={handleDragQ}
            handleDrop={handleDropQ}
            setParentDropable={setParentDropable}
            />
        ))}
      </AnimateSections>
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
          <Modal
            t={t}
            element='section'
            handleOkDelete={handleOkDelete}
            handleConfirm={handleConfirm}
          />
        )
      }
    </div>
  )
})

export default Section;
