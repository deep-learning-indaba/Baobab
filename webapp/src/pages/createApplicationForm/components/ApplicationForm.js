import React, { useState, useEffect, createRef } from 'react';
import { Redirect, Prompt } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Trans } from 'react-i18next';
import { default as ReactSelect } from "react-select";
import _ from 'lodash';
import {
  applicationFormService,
  updateApplicationForm,
  createApplicationForm
} from '../../../services/applicationForm/applicationForm.service';
import { eventService } from '../../../services/events';
import icon from '../icon.svg';
import Section from './Section';
import Loading from '../../../components/Loading';
import {
  option, langObject, AnimateSections,
  drop, drag
 } from './util';


const ApplicationForm = (props) => {
  const { languages } = props;
  const { t } = useTranslation();
  const lang = languages;
  const [nominate, setNominate] = useState(false);
  const [formDetails, setFormDetails] = useState({});

  const [language, setLanguage] = useState({
    label: lang && lang[0]? lang[0].description : 'English',
    value: lang && lang[0]? lang[0].code : 'en'
  });

  const [dragId, setDragId] = useState();
  const [applyTransition, setApplytransition] = useState(false);
  const [parentDropable, setParentDropable] = useState(true);
  const [homeRedirect, setHomeRedirect] = useState(false);
  const [isInCreateMode, setCreateMode] = useState(false);
  const [initialState, setInitialState] = useState(null);
  const [errorResponse, setErrorResponse] = useState(null);
  const [disableSaveBtn, setDisableSaveBtn] = useState(false)

  const [event, setEvent] = useState({
    loading: true,
    event: null,
    error: null,
  });


  const [sections, setSections] = useState([{
    id: `${Math.random()}`,
    name: langObject(lang, t('Untitled Section')),
    description: langObject(lang, ''),
    order: 1,
    depends_on_question_id: 0,
    show_for_values: langObject(lang, null),
    key: null,
    questions: [
      {
        id: `${Math.random()}`,
        surrogate_id: 1,
        description: langObject(lang, ''),
        order: 1,
        headline: langObject(lang, ''),
        placeholder: langObject(lang, ''),
        type: null,
        options: langObject(lang, null),
        value: langObject(lang, ''),
        label: langObject(lang, ''),
        required: false,
        key: null,
        depends_on_question_id: 0,
        show_for_values: langObject(lang, null),
        validation_regex: langObject(lang, null),
        validation_text: langObject(lang, ''),
      }
    ]
  }]);
  const [isSaved, setIsSaved] = useState(false);
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
    const eventId = props.event.id;
    eventService.getEvent(eventId).then( res => {
      setEvent({
        loading: false,
        event: res.event,
        error: res.error
      })
    });
    applicationFormService.getDetailsForEvent(eventId)
      .then(res => {
        if (res) {
          const formSpec = res.formSpec;
          if (formSpec.sections) {
            const mapedQuestions = formSpec.sections.map(s => {
              const questions = s.questions.map(q => {
                const type = q.type;
                q = {
                  ...q,
                  id: `${Math.random()}`,
                  backendId: q.id,
                  required: q.is_required,
                  type: type === 'long_text' ? 'long-text' : type
                }
                return q
              });
              s = {
                ...s,
                id: `${Math.random()}`,
                backendId: s.id,
                questions: questions
              }
              return s
            })
  
            setNominate(formSpec.nominations);
            setFormDetails({
              isOpen: props.event.is_application_open,
              id: formSpec.id,
              eventId: eventId
            })
            setInitialState(mapedQuestions);
            setSections(mapedQuestions);
          } else {
            setFormDetails({
              isOpen: props.event.is_application_open,
              eventId: eventId
            })
            setCreateMode(true);
          }
        } else {
          setFormDetails({
            isOpen: props.event.is_application_open,
            eventId: eventId
          })
          setCreateMode(true);
        }
      }).catch(err => {
        setErrorResponse('Error occured ' + err)
    })
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

  const addSection = () => {
    setTimeout(() => setSections([...sections, {
      id: `${Math.random()}`,
      name: langObject(lang, t('Untitled Section')),
      description: langObject(lang, ''),
      order: sections.length + 1,
      key: null,
      depends_on_question_id: 0,
      show_for_values: langObject(lang, null),
      questions: [
        {
          id: `${Math.random()}`,
          surrogate_id: maxSurrogateId + 1,
          description: langObject(lang, ''),
          order: 1,
          headline: langObject(lang, ''),
          placeholder: langObject(lang, ''),
          type: null,
          options: langObject(lang, null),
          value: langObject(lang, ''),
          label: langObject(lang, ''),
          required: false,
          key: null,
          depends_on_question_id: 0,
          show_for_values: langObject(lang, null),
          validation_regex: langObject(lang, null),
          validation_text: langObject(lang, ''),
        }
      ]
    }]), 1);
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

  const handleSave = async () => {
    const sectionsToSave = sections.map(s => {
      const questions = s.questions.map(q => {
        if (q.backendId) {
          q = {
            id: q.backendId,
            depends_on_question_id: q.depends_on_question_id,
            headline: q.headline,
            description: q.description,
            is_required: q.required,
            key: q.key,
            options: q.options,
            order: q.order,
            placeholder: q.placeholder,
            show_for_values: q.show_for_values,
            type: q.type,
            validation_regex: q.validation_regex,
            validation_text: q.validation_text
          }
        } else {
          q = {
            surrogate_id: q.surrogate_id,
            depends_on_question_id: q.depends_on_question_id,
            headline: q.headline,
            description: q.description,
            is_required: q.required,
            key: q.key,
            options: q.options,
            order: q.order,
            placeholder: q.placeholder,
            show_for_values: q.show_for_values,
            type: q.type,
            validation_regex: q.validation_regex,
            validation_text: q.validation_text
          }
        }
        return q
      });
      if (s.backendId) {
        s = {
          id: s.backendId,
          depends_on_question_id: s.depends_on_question_id,
          description: s.description,
          key: s.key,
          name: s.name,
          order: s.order,
          show_for_values: s.show_for_values,
          questions: questions
        }
      } else {
        s = {
          depends_on_question_id: s.depends_on_question_id,
          description: s.description,
          key: s.key,
          name: s.name,
          order: s.order,
          show_for_values: s.show_for_values,
          questions: questions
        }
      }
      return s
    });
    const { id, eventId, isOpen } = formDetails;
    if (!isInCreateMode) {
      console.log('IS update mode')
      if (!isSaved) {
        const res = await updateApplicationForm(id, eventId, isOpen, nominate, sectionsToSave);
        if(res.status === 200) {
          setIsSaved(true);
          setHomeRedirect(true);
        } else {
          if (res.data && res.data.message) {
            setErrorResponse(res.data.message.event_id);
          } else {
            setErrorResponse(res);
          }
        }
      }
    } else {
      console.log('IS create mode')
        const res = await createApplicationForm(eventId, isOpen, nominate, sectionsToSave);
        console.log(res);
        if (res.status === 201) {
          setIsSaved(true);
          setHomeRedirect(true);
        } else {
          if (res.data && res.data.message) {
            setErrorResponse(res.data.message.event_id);
          } else {
            setErrorResponse(res);
          }
        }
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

  const dateFormat = (date) => {
    return new Date(date).toLocaleDateString('en-GB', {
      weekday: 'short',
      month: 'long',
      day: '2-digit',
      year: 'numeric',
      hour: '2-digit'
    })
  }

  const TopBar = () => {
    return (
      <div className="top-bar">
        <div className="icon-title">
          <img src={icon} alt="form" className="icon" />
          <span className="title">{t("Application Form")}</span>
        </div>
      </div>
    );
  }

  const {loading, event: evnt, error } = event;

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
  return (
    <>
      <Prompt
        when={!isSaved && !saved}
        message="Some Changes have not been saved. Are you sure you want to leave without saving them?"
        />
      {homeRedirect && <Redirect to="/" />}
      {errorResponse ? (
        <div className='tooltiptext-error response-error'>
          <Trans i18nKey='errorResponse' className='response-error'>{{errorResponse}}</Trans>
        </div>
      ) : (
        <div className='application-form-wrap'>
          <TopBar />
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
              className='save-form-btn'
              data-title="Save"
              onClick={handleSave}
              disabled={isSaveDisabled || disableSaveBtn}
              />
          </div>
          <div className="application-form-wrapper">
            <div className="nominations-desc">
              <input
                id="nomination-chck"
                className="nomination-chck"
                type="checkbox"
                checked={nominate}
                onChange={e => handleCheckChanged(e)}
              />
              <span htmlFor="nomination-chck" className="nomination-info">
                {t('Allow candidates to nominate others using this application form'
                + '(Users will be able to submit multiple nominations, including for themselves.'
                + ' If this option is unchecked, a candidate can only apply for themselves)')}
              </span>
            </div>
            <div className="dates-container">
              <span className="dates">
                {t('Application opens ') + ' :'}
                <span className="date">
                  {`${dateFormat(evnt.application_open)}`}
                </span>
              </span>
              <span className="dates">
                {t('Application closes ') + ' :'}
                <span className="date">
                  {`${dateFormat(evnt.application_close)}`}
                </span>
              </span>
            </div>
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

export default ApplicationForm;