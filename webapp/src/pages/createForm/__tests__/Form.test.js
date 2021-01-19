import React from 'react';
import { shallow } from 'enzyme';
// import Application from '../Application.js';
import Form from '../components/ApplicationForm';

test('Check if Application Form Page renders.', () => {
  // Render Application Form Page.
  const wrapper = shallow(<Form />);
  expect(wrapper.length).toEqual(1);
});
