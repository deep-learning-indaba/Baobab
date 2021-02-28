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

export const Section = forwardRef(({
  t, sectionIndex, sections, inputs, lang,
  setSection, handleDrag, handleDrop,
  setApplytransition, setParentDropable, parentDropable
}, ref) => {
  const [isModelVisible, setIsModelVisible] = useState(false);
  const [questionAnimation, setQuestionAnimation] = useState(false);
  const [dragId, setDragId] = useState();
  const [showingQuestions, setShowingQuestions] = useState(true);

  const handleChange = (prop) => (e) => {
    const target = inputs[prop];
    const updatedSections = sections.map(s => {
      if(s.id === inputs.id) {
        s = {...s, [prop]: {...target, [lang]: e.target.value}};
      }
      return s;
    });
    setSection(updatedSections);
    setApplytransition(false);
  }

  const addQuestion = () => {
    const qsts = inputs.questions;
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
      if (s.id === inputs.id) {
        s = {...inputs, questions: [...qsts, qst]};
      }
      return s;
    });
    setSection(updatedSections);
    setApplytransition(false);
    setQuestionAnimation(false);
  }

  const handleOkDelete = () => {
    const updatedSections = sections.filter(s => s.id !== inputs.id);
    setSection(updatedSections);
  }

  const handleConfirm = () => {
    setIsModelVisible(!isModelVisible);
  }

  const handleMoveSectionUp = () => {
    handleMove({
      elements: sections,
      index: sectionIndex,
      setState: setSection,
      setAnimation: setApplytransition,
      isUp: true
    });
  }

  const handleMoveSectionDown = () => {
    handleMove({
      elements: sections,
      index: sectionIndex,
      setState: setSection,
      setAnimation: setApplytransition
    });
  }

  const handleDragQuestion = (e) => {
    drag(e, setDragId);
    setParentDropable(false);
  };

  const handleDropQuestion = (e) => {
    drop({
      event: e,
      elements: inputs.questions,
      dragId,
      section: inputs,
      setAnimation: setQuestionAnimation,
      setSection: setSection,
      sections
    });
    setParentDropable(false);
    setApplytransition(false);
  }

  const handleMouseDown = () => {
    setParentDropable(true);
  };

  const showQuestions = () => {
    setShowingQuestions(!showingQuestions);
    setQuestionAnimation(false);
  }

  const numSections = sections.length;
  const index = sectionIndex + 1;
  const isDeleteDisabled = sections.length === 1 ? true : false;
  return (
    <div
      className="section-wrapper"
      id={inputs.id}
      key={inputs.id}
      ref={ref}
      draggable={parentDropable}
      onDragOver={e => e.preventDefault()}
      onDragStart={handleDrag}
      onDrop={handleDrop}
    >
      <div
        className="section-number"
        onMouseDown={handleMouseDown}
        style={{ cursor: 'grab'}}
      >
        <Trans i18nKey='sectionPlace' >Section {{index}} of {{numSections}}</Trans>
      </div>
      <div className="title-description">
        <div className="section-header">
          <input
            type="text"
            value={inputs.name[lang]}
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
              disabled={isDeleteDisabled}
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
              onClick={handleMoveSectionUp}
              disabled={index === 1}
            >
              <i class="fas fa-angle-up fa-section fa-duplicate"></i>
              {t("Move Section Up")}
            </button>
            <button
              disabled={index === sections.length}
              className="dropdown-item delete-section"
              onClick={handleMoveSectionDown}
            >
              <i class="fas fa-angle-down fa-section fa-duplicate"></i>
              {t("Move Section Down")}
            </button>
          </div>
          
        </div>
        <input
          name="section-desc"
          type="text"
          value={inputs.description[lang]}
          placeholder={t('Description')}
          onChange={handleChange('description')}
          className="section-inputs section-desc"
          /> 
      </div>
      <div className="arrow-wrapper">
        <button className="arrow-btn" onClick={showQuestions}>
          <i
            className="arrow-btns"
            style={showingQuestions ? { transform: 'rotate(45deg) skew(120deg, 120deg)'}
              : { transform: 'rotate(-135deg) skew(120deg, 120deg)'}}></i>
        </button>
      </div>
      <AnimateSections
        applyTransition={questionAnimation}
        setApplytransition={setQuestionAnimation}
      >
        {inputs.questions.map((question, i) => (
          <Question
            inputs={question}
            key={question.id}
            t={t}
            ref={createRef()}
            num={question.id}
            questions={inputs.questions}
            setSections={setSection}
            sections={sections}
            sectionId={inputs.id}
            section={inputs}
            lang={lang}
            setApplytransition={setApplytransition}
            questionIndex={i}
            setQuestionAnimation={setQuestionAnimation}
            handleDrag={handleDragQuestion}
            handleDrop={handleDropQuestion}
            setParentDropable={setParentDropable}
            parentDropable={parentDropable}
            showingQuestions={showingQuestions}
            />
        ))}
      </AnimateSections>
      <div
        className='add-question-wrapper'
      >
        <button
          className="add-question-btn"
          data-title={t('Add Question')}
          onMouseUp={() => addQuestion()}
          style={!showingQuestions ? {display: 'none'}: {}}
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
