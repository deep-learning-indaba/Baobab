import React, { useEffect, createRef } from 'react';
import { Redirect, Prompt } from 'react-router-dom';
import { Trans } from 'react-i18next';
import { default as ReactSelect } from "react-select";
import _ from 'lodash';
import Section from '../../pages/createApplicationForm/components/Section';
import Loading from '../Loading';
import {
  option, AnimateSections,
  drop, drag, Stages, StageModal
 } from '../../pages/createApplicationForm/components/util';
 import { dateFormat, TopBar } from '../../utils/forms';
 


const FormCreator = ({
  languages, event: evt, t, sections,
  setSections, nominate, setNominate,
  language, setLanguage, dragId, setDragId,
  applyTransition, setApplytransition,
  parentDropable, setParentDropable,
  homeRedirect, initialState, errorResponse,
  disableSaveBtn, setDisableSaveBtn,
  events, setEvent, eventService, addSection,
  handleSave, isSaved, isReview, addQuestion,
  addAnswerFromAppForm, appSections, stage,
  setCurrentStage, currentStage, leaveStage,
  setLeaveStage, showingModal, setShowingModal,
  isNewStage, setIsNewStage, title, EventMeta,
  hasKey, hasDependancy, hasSpecialQuestion
}) => {
  const lang = languages;

  const saved = _.isEqual(initialState, sections);
  let maxSurrogateId = 1;
  sections.forEach(s => {
    if (s.backendId > maxSurrogateId) {
      maxSurrogateId = s.backendId;
    }
    s.questions.forEach(q => {
      if (q.backendId > maxSurrogateId) {
        maxSurrogateId = q.backendId
      }
      if (q.surrogate_id > maxSurrogateId) {
        maxSurrogateId = q.surrogate_id
      }
    })
  })

  useEffect(() => {
    const eventId = evt.id;
    eventService.getEvent(eventId).then( res => {
      setEvent({
        loading: false,
        event: res.event,
        error: res.error
      })
    });
  }, []);

  const handleCheckChanged = (e) => {
    const val = e.target.checked;
    setTimeout(() => {
      setNominate(val);
    }, 1);
  }

  const handleLanguageChange = (e) => {
    setLanguage(e);
  }

  const handleSection = (input) => {
    setSections(input);
  }

  const handleDrag = (e) => {
    if(parentDropable) {
      drag(e, setDragId);
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    if (parentDropable) {
      drop({
        event: e,
        elements: sections,
        dragId,
        setState: setSections,
        setAnimation: setApplytransition
      });
    }
  }

  const options = () => {
    return lang.map(l => option({
      value: l.code,
      label: l.description,
      t
    }));
  }

  let isSaveDisabled = false;
  sections.forEach(s => {
    for(let key of Object.keys(s.name)) {
      if (!s.name[key]) {
        isSaveDisabled = true;
      }
    }
    s.questions.forEach(q => {
      for(let key of Object.keys(q.headline)) {
        if (!q.headline[key]) {
          isSaveDisabled = true;
        }
      }
      if (!q.type) {
        isSaveDisabled = true;
      }
    })
  })

  

  const {loading, event: evnt, error } = events;

  if (loading) {
    return <Loading />
  }
  if (error) {
    return (
      <div className='alert alert-danger alert-container'>
        {error}
      </div>
    )
  }
  const eventId = evt.id;

  return (
    <>
      <Prompt
        when={!isSaved && !saved}
        message="Some Changes have not been saved. Are you sure you want to leave without saving them?"
        />
      {homeRedirect && <Redirect to={`/${eventId}`} />}
      {errorResponse ? (
        <div className='tooltiptext-error response-error'>
          <Trans i18nKey='errorResponse' className='response-error'>{{errorResponse}}</Trans>
        </div>
      ) : (
        <div className='application-form-wrap'>
          <TopBar
            title={title}
            t={t} />
          <div
            style={{ textAlign: 'end', width: '61%' }}
            className='add-section-btn-wrapper'
            >
            <button
              className='add-section-btn'
              data-title="Add Section"
              onMouseUp={() => addSection()}
              >
              <i className="fas fa-plus fa-lg add-section-icon"></i>
            </button>
            <input
              type="button"
              value="Save"
              style={!isReview ? { marginTop: '16em'} : {}}
              className='save-form-btn'
              data-title="Save"
              onClick={handleSave}
              disabled={isSaveDisabled || disableSaveBtn}
              />
          </div>
          <div className="application-form-wrapper">
            <EventMeta
              dateFormat={dateFormat}
              handleCheckChanged={handleCheckChanged}
              saved={saved}
              evnt={evnt}
              />
            <ReactSelect
              id='select-language'
              options={options()}
              onChange={e => handleLanguageChange(e)}
              value={language}
              defaultValue={language}
              className='select-language'
              styles={{
                control: (base, state) => ({
                  ...base,
                  boxShadow: "none",
                  border: state.isFocused && "none",
                  transition: state.isFocused && 'color,background-color 1.5s ease-out',
                  background: state.isFocused && 'lightgray',
                  color: '#fff'
                }),
                option: (base, state) => ({
                    ...base,
                    backgroundColor: state.isFocused && "#1f2d3e",
                    color: state.isFocused && "#fff"
                })
              }}
              menuPlacement="auto"
            />
            {!saved && !leaveStage && showingModal && (
              <StageModal
                t={t}
                setLeaveStage={setLeaveStage}
                setShowingModal={setShowingModal}
                setIsNewStage={setIsNewStage}
              />
            )}
            <AnimateSections
              applyTransition={applyTransition}
              setApplytransition={setApplytransition}
            >
              {
                sections
                .map((section, i) => (
                  <Section
                    t={t}
                    key={section.id}
                    id={section.id}
                    sectionIndex={i}
                    setSection={handleSection}
                    inputs={section}
                    sections={sections}
                    addSection={addSection}
                    lang={language.value}
                    langs={lang}
                    ref={createRef()}
                    handleDrag={handleDrag}
                    handleDrop={handleDrop}
                    setApplytransition={setApplytransition}
                    handleDragOver={handleDragOver}
                    setParentDropable={setParentDropable}
                    parentDropable={parentDropable}
                    setDisableSaveBtn={setDisableSaveBtn}
                    isReview={isReview}
                    addQuestion={addQuestion}
                    addAnswerFromAppForm={addAnswerFromAppForm}
                    appSections={appSections}
                    hasKey={hasKey}
                    hasDependancy={hasDependancy}
                    hasSpecialQuestion={hasSpecialQuestion}
                  />
                ))
              }
            </AnimateSections>
          </div>
        </div>
      )}
    </>
  )
}

export default FormCreator;
