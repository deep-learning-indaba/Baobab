import React, { useState, useEffect, createRef } from 'react';
import { useTranslation } from 'react-i18next'
import { default as ReactSelect } from "react-select";
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

  const [language, setLanguage] = useState({
    label: lang && lang[0]? lang[0].description : 'English',
    value: lang && lang[0]? lang[0].code : 'en'
  });

  const [dragId, setDragId] = useState();
  const [applyTransition, setApplytransition] = useState(false);

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
    questions: [
      {
        id: `${Math.random()}`,
        order: 1,
        headline: langObject(lang, ''),
        placeholder: langObject(lang, ''),
        type: null,
        options: langObject(lang, []),
        value: langObject(lang, ''),
        label: langObject(lang, ''),
        required: false
      }
    ]
  }]);

  useEffect(() => {
    eventService.getEvent(props.event.id).then( res => {
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
    setApplytransition(true);
    setSections(input);
  }

  const addSection = () => {
    setTimeout(() => setSections([...sections, {
      id: `${Math.random()}`,
      name: langObject(lang, t('Untitled Section')),
      description: langObject(lang, ''),
      order: sections.length + 1,
      questions: [
        {
          id: `${Math.random()}`,
          order: 1,
          headline: langObject(lang, ''),
          placeholder: langObject(lang, ''),
          type: null,
          options: langObject(lang, []),
          value: langObject(lang, ''),
          label: langObject(lang, ''),
          required: false
        }
      ]
    }]), 1);
    setApplytransition(false);
  }

  const handleDrag = (e) => {
    drag(e, setDragId);
  }

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    drop({
      event: e,
      elements: sections,
      dragId,
      setState: setSections,
      setAnimation: setApplytransition
    });
    setApplytransition(false);
  }

  const options = () => {
    return lang.map(l => option({
      value: l.code,
      label: l.description,
      t
    }));
  }

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
        <button className="create-form-btn">{t("Save")}</button>
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
      <div className='application-form-wrap'>
        <TopBar />
        <div style={{ textAlign: 'end', width: '61%' }}>
          <button
            className='add-section-btn'
            data-title="Add Section"
            onMouseUp={() => addSection()}
          >
            <i class="fas fa-plus fa-lg add-section-icon"></i>
          </button>
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
                ref={createRef()}
                handleDrag={handleDrag}
                handleDrop={handleDrop}
                setApplytransition={setApplytransition}
                handleDragOver={handleDragOver}
              />
            ))
          }
        </AnimateSections>
      </div>
      </div>
    </>
  )
}

export default ApplicationForm;