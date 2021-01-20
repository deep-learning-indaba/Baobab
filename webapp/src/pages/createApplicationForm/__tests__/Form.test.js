import React from 'react';
import { shallow } from 'enzyme';
import ApplicationForm from '../components/ApplicationForm';
import Section from '../components/Section';
import Question from '../components/Question';
import Form from '../Form';

test('Check if Application Form Page renders.', () => {
  // Render Application Form Page.
  const props = {
    event: {
      id: '2021'
    }
  }
  const wrapper = shallow(<ApplicationForm {...props} />);
  expect(wrapper.length).toEqual(1);
});

test('Check if the Section Component renders.', () => {
  // Render Section Component.
  const num = 1;
  const t = jest.fn();
  const setSection = jest.fn();
  const sections = [];
  const inputs = {
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
    };
  const addSection = jest.fn(); 
  const addQuestion = jest.fn();
  const props = {
    num,
    setSection,
    sections,
    inputs,
    addSection,
    addQuestion,
    t
  };
  const wrapper = shallow(<Section {...props} />);
  expect(wrapper.length).toEqual(1);
});

test('Check if the Question Component renders.', () => {
  // Render Question Component.
  const num = 1;
  const t = jest.fn();
  const questions = [{
    id: `${Math.random()}`,
    order: 1,
    headline: '',
    placeholder: '',
    type: null,
    options: [],
    value: '',
    label: '',
    required: false
  }];
  const inputs = {
    id: `${Math.random()}`,
    order: 1,
    headline: '',
    placeholder: '',
    type: null,
    options: [],
    value: '',
    label: '',
    required: false
  };
  const setQuestions = jest.fn();
  const props = {
    num,
    setQuestions,
    questions,
    inputs,
    t
  };
  const wrapper = shallow(<Question {...props} />);
  expect(wrapper.length).toEqual(1);
});

test('Check if the Form Component renders', () => {
  const wrapper = shallow(<Form />);
  expect(wrapper.length).toEqual(1);
})
