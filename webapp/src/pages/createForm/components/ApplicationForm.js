import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next'
import { eventService } from '../../../services/events';
import icon from '../icon.svg';
import Section from './Section';

const ApplicationForm = (props) => {
  const [nominate, setNominate] = useState(false);
  const [event, setEvent] = useState({
    loading: true,
    event: null,
    error: null,
  });
  const [sections, setSections] = useState([{
    id: 1,
    name: 'Untitled Section',
    description: '',
    questions: [
      {
        id: `${Math.random()}`,
        order: 1,
        headline: '',
        placeholder: '',
        type: null,
        options: [],
        value: '',
        label: '',
        required: false
      }
    ]
  }]);
  const { t } = useTranslation();

  useEffect(() => {
    eventService.getEvent(props.event.id).then( res => {
      setEvent({
        loading: res.loading,
        event: res.event,
        error: res.error
      })
    })
  }, []);
  const handleCheckChanged = (e) => {
    setNominate(e.target.checked);
  }
  const handleSection = (input) => {
    setSections(input)
  }
  const addSection = () => {
    const id = sections.length + 1;
    setSections([...sections, {
      id: id,
      name: 'Untitled Section',
      description: '',
      questions: [
        {
          id: 1,
          order: 1,
          headline: '',
          placeholder: '',
          type: null,
          options: [],
          value: '',
          label: '',
          required: false
        }
      ]
    }]);
  }
  const addQuestion = (id) => {
    let newSections = sections.map(e => {
      if(e.id === id) {
        return {...e, questions: [...e.questions, {
          id: `${Math.random()}`,
          order: e.questions.length && e.questions.length + 1,
          headline: '',
          placeholder: '',
          type: null,
          options: [],
          value: '',
          label: '',
          required: false
        }]}
      }
      return e;
    });
    setSections(newSections);
  } 
  const dateFormat = (date) => {
    return new Date(date).toLocaleDateString('en-US', {
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
          <span className="title">{t("Form title")}</span>
        </div>
        <button className="create-form-btn">{t("Save")}</button>
      </div>
    );
  }
  const FormSection = () => {
    const {loading, event: evnt, error } = event;
 
    if (loading) {
      return (
        <div>
          <i className="fa fa-spinner fa-lg" aria-hidden="true"></i>
        </div>
      )
    }
    if (error) {
      return (
        <div>{error}</div>
      )
    }

    return (
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
        {
          sections.map(section => (
            <Section
              t={t}
              key={section.id}
              num={section.id}
              setSection={handleSection}
              inputs={section}
              sections={sections}
              addSection={addSection}
              addQuestion={addQuestion}
            />
          ))
        }
      </div>
    )
  }
  return (
    <>
      <TopBar />
      <FormSection />
    </>
  )
}

export default ApplicationForm;