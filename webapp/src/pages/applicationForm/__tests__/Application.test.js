import React from 'react';
import { shallow } from 'enzyme';
import Application from '../Application.js';
import ApplicationForm from '../components/ApplicationForm';
import FormDate from '../../../components/form/FormDate';

test('Check if Application Form Page renders.', () => {
  // Render Application Form Page.
  const wrapper = shallow(<Application />);
  expect(wrapper.length).toEqual(1);
});


