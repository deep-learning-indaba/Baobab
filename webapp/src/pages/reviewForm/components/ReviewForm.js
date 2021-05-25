import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  applicationFormService,
  updateApplicationForm,
  createApplicationForm
} from '../../../services/applicationForm/applicationForm.service';
import { langObject } from '../../../pages/createApplicationForm/components/util';
import { eventService } from '../../../services/events';
import { reviewService } from '../../../services/reviews';
import FormCreator from '../../../components/form/FormCreator';

const ReviewForm = (props) => {
  const { languages } = props;
  const { t } = useTranslation();
  const lang = [...languages, {code: 'fr', description: 'French'}];
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
  const [stage, setStage] = useState({
    loading: true,
    stage: null,
    error: null,
  });
  const [appSections, setAppSections] = useState([]);
  // console.log('$$$ ', appSections);


  const [sections, setSections] = useState([{
    id: `${Math.random()}`,
    name: langObject(lang, t('Untitled Section')),
    description: langObject(lang, ''),
    order: 1,
    show_for_values: langObject(lang, null),
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
        show_for_values: langObject(lang, null),
        validation_regex: langObject(lang, null),
        validation_text: langObject(lang, ''),
        weight: 0,
      }
    ]
  }]);
  const [isSaved, setIsSaved] = useState(false);
  // const saved = _.isEqual(initialState, sections);
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
    reviewService.getReviewStage(eventId)
    .then(res => {
      setStage({
        loading: false,
        stage: res.data,
        error: res.error
      })
    });
    applicationFormService.getDetailsForEvent(eventId)
      .then(res => {
        const formSpec = res.formSpec;
        const sections = formSpec && formSpec.sections;
        if (sections) {
          setAppSections(sections);
        }
      })
  }, []);

  const addSection = () => {
    setTimeout(() => setSections([...sections, {
      id: `${Math.random()}`,
      name: langObject(lang, t('Untitled Section')),
      description: langObject(lang, ''),
      order: sections.length + 1,
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
          show_for_values: langObject(lang, null),
          validation_regex: langObject(lang, null),
          validation_text: langObject(lang, ''),
          weight: 0,
        }
      ]
    }]), 1);
  }

  const addQuestion = (sectionId) => {
    const surrogateId = maxSurrogateId + 1
    const sction = sections.filter(s => s.id === sectionId);
    const qsts = sction.questions;
    const qst = {
      id: `${Math.random()}`,
      surrogate_id: surrogateId,
      description: langObject(lang, ''),
      order: qsts.length + 1,
      headline: langObject(lang, ''),
      placeholder: langObject(lang, ''),
      type: null,
      options: langObject(lang, null),
      value: langObject(lang, ''),
      label: langObject(lang, ''),
      required: false,
      show_for_values: langObject(lang, null),
      validation_regex: langObject(lang, null),
      validation_text: langObject(lang, ''),
      weight: 0,
    }
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...s, questions: [...qsts, qst]};
      }
      return s;
    });
    setSections(updatedSections);
    setApplytransition(false);
    // setQuestionAnimation(false);
  }

  const addAnswerFromAppForm = (sectionId) => {
    const surrogateId = maxSurrogateId + 1;
    const sction = sections.find(s => s.id === sectionId);
    const qsts = sction.questions;
    const qst = {
      id: `${Math.random()}`,
      surrogate_id: surrogateId,
      description: langObject(lang, ''),
      order: qsts.length + 1,
      headline: langObject(lang, ''),
      type: 'information',
      required: false,
      question_id: null,
    }
    const updatedSections = sections.map(s => {
      if (s.id === sectionId) {
        s = {...s, questions: [...qsts, qst]};
      }
      return s;
    });
    setSections(updatedSections);
    setApplytransition(false);
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
      // console.log('IS update mode')
      // if (!isSaved) {
      //   const res = await updateApplicationForm(id, eventId, isOpen, nominate, sectionsToSave);
      //   if(res.status === 200) {
      //     setIsSaved(true);
      //     setHomeRedirect(true);
      //   } else {
      //     if (res.data && res.data.message) {
      //       setErrorResponse(res.data.message.event_id);
      //     } else {
      //       setErrorResponse(res);
      //     }
      //   }
      // }
    } else {
        // const res = await createApplicationForm(eventId, isOpen, nominate, sectionsToSave);
        // console.log(res);
        // if (res.status === 201) {
        //   setIsSaved(true);
        //   setHomeRedirect(true);
        // } else {
        //   if (res.data && res.data.message) {
        //     setErrorResponse(res.data.message.event_id);
        //   } else {
        //     setErrorResponse(res);
        //   }
        // }
    }
  }

  return (
    <FormCreator
      languages={lang}
      event={props.event}
      t={t}
      sections={sections}
      setSections={setSections}
      language={language}
      setLanguage={setLanguage}
      dragId={dragId}
      setDragId={setDragId}
      applyTransition={applyTransition}
      setApplytransition={setApplytransition}
      parentDropable={parentDropable}
      setParentDropable={setParentDropable}
      homeRedirect={homeRedirect}
      initialState={initialState}
      errorResponse={errorResponse}
      disableSaveBtn={disableSaveBtn}
      setDisableSaveBtn={setDisableSaveBtn}
      events={event}
      setEvent={setEvent}
      eventService={eventService}
      addSection={addSection}
      handleSave={handleSave}
      isSaved={isSaved}
      isReview={true}
      addQuestion={addQuestion}
      addAnswerFromAppForm={addAnswerFromAppForm}
      appSections={appSections}
      stage={stage}
     />
  )
}

export default ReviewForm;