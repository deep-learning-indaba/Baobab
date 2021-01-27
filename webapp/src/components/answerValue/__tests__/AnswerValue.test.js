import React from 'react';
import { shallow } from 'enzyme';

import AnswerValue from '../AnswerValue';
import MultiFileValue from '../MultiFileValue'

const baseUrl = process.env.REACT_APP_API_URL;

jest.mock('react-i18next', () => ({
  // this mock makes sure any components using the translate HoC receive the t function as a prop
  withTranslation: () => Component => {
      Component.defaultProps = { ...Component.defaultProps, t: v => v };
      return Component;
  },
}));

describe('AnswerValue Tests', () => {

  it('Renders AnswerValue component.', () => {
    const answer = {
      value: 'Lorem'
    }
    const question = {
      type: 'information'
    }
    const wrapper = shallow(
      <AnswerValue answer={answer} question={question} />
    );
    expect(wrapper.length).toEqual(1);
  });

  it('Renders file.', () => {
    const answer = {value: 'lorem.txt'}
    const question = {type: 'file'}
    const wrapper = shallow(
      <AnswerValue answer={answer} question={question} />
    );
    const href = baseUrl + "/api/v1/file?filename=" + answer.value
    expect(wrapper.contains(
      <a target="_blank" href={href}>
        Uploaded File
      </a>
    )).toEqual(true);
  });

  it('Renders multi-file.', () => {
    const answer = {value: ['lorem.txt']}
    const question = {type: 'multi-file'}
    const wrapper = shallow(
      <AnswerValue answer={answer} question={question} />
    );
    expect(wrapper.contains(
      <MultiFileValue value={answer.value}/>
    ));
  });

  it('Renders nothing for "information" type.', () => {
    const answer = {}
    const question = {
      type: 'information'
    }
    const wrapper = shallow(
      <AnswerValue answer={answer} question={question} />
    );
    expect(wrapper.equals("")).toEqual(true);
  });

  it('Renders nothing for "information" answer question type.', () => {
    const answer = {question_type: 'information'}
    const question = {}
    const wrapper = shallow(
      <AnswerValue answer={answer} question={question} />
    );
    expect(wrapper.equals("")).toEqual(true);
  });

  it('Renders multi-choice.', () => {
    const answer = {
      value: 'ipsum'
    }
    const question = {
      type: 'multi-choice',
      options: [
        { label: 'Lorem', value: 'lorem' },
        { label: 'Ipsum', value: 'ipsum' },
        { label: 'Dolor', value: 'dolor' }
      ]
    }
    const wrapper = shallow(
      <AnswerValue answer={answer} question={question} />
    );
    expect(wrapper.equals("Ipsum")).toEqual(true);
  });

  it('Renders "No answer provided" when answer has no value.', () => {
    const answer = {value: null}
    const question = {
      type: 'multi-choice',
      options: [
        { label: 'Lorem', value: 'lorem' },
        { label: 'Ipsum', value: 'ipsum' },
        { label: 'Dolor', value: 'dolor' }
      ]
    }
    const wrapper = shallow(
      <AnswerValue answer={answer} question={question} />
    );
    expect(wrapper.equals("No answer provided.")).toEqual(true);
  });

  it('Renders answer value for all other types.', () => {
    const answer = { value: 'lorem' }
    const question = { type: 'ipsum' }
    const wrapper = shallow(
      <AnswerValue answer={answer} question={question} />
    );
    expect(wrapper.equals("lorem")).toEqual(true);
  });

});