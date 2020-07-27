import React from 'react';
import {shallow, mount} from 'enzyme';
import Application from '../Application.js';
import Section from '../components/ApplicationForm';

test('Check if Application Form Page renders.', () => {
  // Render Application Form Page.
  const wrapper = shallow(<Application />);
  expect(wrapper.length).toEqual(1);
});

describe('Check if validate failure renders error in FormDate component UI', () => {
  it('FormDate error', () => {

  const wrapper = shallow(<Section.WrappedComponent />);

  let result = wrapper.instance().validate();

  expect(result).toEqual("error")
  })
})
