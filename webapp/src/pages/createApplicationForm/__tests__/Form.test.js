import React from 'react';
import { shallow } from 'enzyme';
import ApplicationForm from '../components/ApplicationForm';
import Section from '../components/Section';
import Question from '../components/Question';
import Form from '../Form';

test('Check if Application Form Page renders.', () => {
  // Render Application Form Page.
  const languages = [{ code: 'en', description: 'English' }];
  const props = {
    event: {
      id: '2021'
    },
    languages
  }
  const wrapper = shallow(<ApplicationForm {...props} />);
  expect(wrapper.length).toEqual(1);
});

test('Check if the Section Component renders.', () => {
  // Render Section Component.
  const t = jest.fn();
  const setSection = jest.fn();
  const sections = [];
  const sectionIndex = 0;
  const lang = 'en';
  const inputs = {
    id: `${Math.random()}`,
    name: {
      en: 'Untitled Section',
      fr: 'Section sans titre'
    },
    description: {
      en: '',
      fr: ''
    },
    questions: [
      {
        id: `${Math.random()}`,
        order: 1,
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
    ]
  };
  const addSection = jest.fn(); 
  const addQuestion = jest.fn();
  const props = {
    setSection,
    sections,
    inputs,
    addSection,
    addQuestion,
    sectionIndex,
    lang,
    t
  };
  const wrapper = shallow(<Section {...props} />);
  expect(wrapper.length).toEqual(1);
});

test('Check if the Question Component renders.', () => {
  // Render Question Component.
  const t = jest.fn();
  const sectionId = 1;
  const section = {
    id: `${Math.random()}`,
    name: {
      en: 'Untitled Section',
      fr: 'Section sans titre'
    },
    description: {
      en: '',
      fr: ''
    },
    language: {label: 'English', value: 'en'},
    questions: [
      {
        id: `${Math.random()}`,
        order: 1,
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
    ]
  }
  const  sections = [{
    id: `${Math.random()}`,
    name: {
      en: 'Untitled Section',
      fr: 'Section sans titre'
    },
    description: {
      en: '',
      fr: ''
    },
    language: {label: 'English', value: 'en'},
    questions: [
      {
        id: `${Math.random()}`,
        order: 1,
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
    ]
  }]
  const lang = 'en';

  const questions = [{
    id: `${Math.random()}`,
    order: 1,
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
  }];
  const inputs = {
    id: `${Math.random()}`,
    order: 1,
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
  };

  const props = {
    questions,
    inputs,
    t,
    sectionId,
    sections,
    lang,
    section
  };
  const wrapper = shallow(<Question {...props} />);
  expect(wrapper.length).toEqual(1);
});

test('Check if the Form Component renders', () => {
  const languages = [{ code: 'en', description: 'English' }];
  const props = {
    languages
  };
  const wrapper = shallow(<Form {...props} />);
  expect(wrapper.length).toEqual(1);
})
