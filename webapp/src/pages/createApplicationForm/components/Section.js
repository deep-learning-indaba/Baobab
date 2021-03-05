import React,
{
  useState, forwardRef, createRef
} from 'react';
import { Trans } from 'react-i18next';
import Question from './Question';
import {
  Modal, AnimateSections, handleMove, langObject,
  drag, drop, option, Dependency, dependencyChange
} from './util';

export const Section = forwardRef(({
  t, sectionIndex, sections, inputs, lang,
  setSection, handleDrag, handleDrop,langs,
  setApplytransition, setParentDropable, parentDropable
}, ref) => {
  const [isModelVisible, setIsModelVisible] = useState(false);
  const [questionAnimation, setQuestionAnimation] = useState(false);
  const [dragId, setDragId] = useState();
  const [showingQuestions, setShowingQuestions] = useState(true);
  const [style, setStyle] = useState({});
  const [hideOrShowDetails, setHideOrShowDetails] = useState(false);

  const handleChange = (prop) => (e) => {
    const target = inputs[prop];
    const updatedSections = sections.map(s => {
      if(s.id === inputs.id) {
        if (prop === 'key') {
          s = {...s, [prop]: e.target.value};
        } else {
          s = {...s, [prop]: {...target, [lang]: e.target.value}};
        }
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
      headline: langObject(langs, ''),
      placeholder: langObject(langs, ''),
      type: null,
      options: langObject(langs, []),
      value: langObject(langs, ''),
      label: langObject(langs, ''),
      required: false,
      key: '',
      depends_on_question_id: null,
      show_for_values: null,
      validation_regex: langObject(langs, ''),
      validation_text: langObject(langs, '')
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
    const questionsInSection = inputs.questions;
    const sectionsWithoutDependency = sections.map(s => {
        questionsInSection.forEach(q => {
          if (s.depends_on_question_id === q.id) {
            s = {...s, depends_on_question_id: null}
          }
        })
      return s;
    })
    const updatedSections = sectionsWithoutDependency.filter(s => s.id !== inputs.id);
    const orderedSections = updatedSections.map((s,i) => {
      return {...s, order: i + 1}
    })
    setSection(orderedSections);
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

  const handleHideHover = () => {
    setStyle({
      backgroundColor: 'rgb(168, 167, 167)',
      cursor: 'pointer'
    });
  }

  const handleMouseOut = () => {
    setStyle({})
  }

  const handleHideOrShowDetails = () => {
    setHideOrShowDetails(!hideOrShowDetails);
  }

  const handlequestionDependency = (e) => {
    const updatedSections = sections.map(s => {
      if (s.id === inputs.id) {
        s = {...inputs, depends_on_question_id: e.value};
      }
      return s;
    });
    setSection(updatedSections);
  }

  const handleDependencyChange = (prop) => (e) => {
    dependencyChange({
      prop:prop,
      e:e,
      sections:sections,
      inputs:inputs,
      setSection:setSection
    })
  }

  const options = [];
  const questions = inputs.questions;
  for(let i = 0; i < questions.length; i++) {
    const opt = option({
      value: `${questions[i].id}`,
      label: questions[i].headline[lang]
        ? questions[i].headline[lang] : questions[i].order,
      t
    })
    opt["order"] = questions[i].order;
    options.push(opt);
  };

  const sectionOptions = [];
  sections.forEach(e => {
    if (e.order < inputs.order) {
      e.questions.forEach(q => {
        const opt = option({
          value: `${q.id}`,
          label: q.headline[lang]
            ? `${e.order}. ${q.headline[lang]}`
            : `${e.order}. ${q.order}`,
            t
        })
        opt['order'] = q.order;
        sectionOptions.push(opt);
      })
    }
  });

  const numSections = sections.length;
  const index = sectionIndex + 1;
  const isDeleteDisabled = sections.length === 1 ? true : false;
  const dependentQuestion = inputs.questions
    .find(e => e.id === inputs.depends_on_question_id);

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
        <span className="key-wrapper">
          <input
            type="text"
            value={inputs.name[lang]}
            onChange={handleChange('name')}
            className="section-inputs section-title"
          />
          <span className="tooltiptext">{t('Title')}</span>
        </span>
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
          <div
            className='toogle-section-details-wrapper'
            onMouseOver={handleHideHover}
            onMouseOut={handleMouseOut}
            onClick={handleHideOrShowDetails}
          >
            {!hideOrShowDetails ? (
              <div className='toogle-section-details' style={style}>
                <i class="fas fa-chevron-down fa-move fa-hide-show-details"></i>
                <i class="fas fa-chevron-up fa-move fa-hide-show-details"></i>
              </div>
            ): 
              <div className='toogle-section-details' style={style}>
                <i class="fas fa-chevron-up fa-move fa-hide-show-details"></i>
                <i class="fas fa-chevron-down fa-move fa-hide-show-details"></i>
              </div>
            }
          </div>
          
        </div>
        <div
          className='desc-dependency-div'
          style={hideOrShowDetails ? {display: 'none'} : {}}
        >
          <div className="key-wrapper">
            <input
              name="section-desc"
              type="text"
              value={inputs.description[lang]}
              placeholder={t('Description')}
              onChange={handleChange('description')}
              className="section-inputs section-desc"
              />
            <span className="tooltiptext">{t('Description')}</span>
          </div>
          <span className="key-wrapper">
            <input
              name="section-desc"
              type="text"
              value={inputs.key}
              placeholder={t('Key')}
              onChange={handleChange('key')}
              className="section-inputs section-desc section-key"
              />
            <span className="tooltiptext">{t('key')}</span>
          </span>
          <Dependency
            options={sectionOptions}
            handlequestionDependency={handlequestionDependency}
            inputs={inputs}
            dependentQuestion={dependentQuestion}
            handleDependencyChange={handleDependencyChange}
            lang={lang}
            t={t}
            />
        </div>
      </div>
      <div className="arrow-wrapper">
        <button
          className="arrow-btn"
          onClick={showQuestions}
        >
          <i
            className="arrow-btns"
            style={showingQuestions 
              ? { transform: 'rotate(45deg) skew(120deg, 120deg)'}
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
            langs={langs}
            setApplytransition={setApplytransition}
            questionIndex={i}
            setQuestionAnimation={setQuestionAnimation}
            handleDrag={handleDragQuestion}
            handleDrop={handleDropQuestion}
            setParentDropable={setParentDropable}
            parentDropable={parentDropable}
            showingQuestions={showingQuestions}
            optionz={options}
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
            inputs={inputs}
            sections={sections}
          />
        )
      }
    </div>
  )
})

export default Section;
