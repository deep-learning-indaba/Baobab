import React from 'react';
import { shallow } from 'enzyme';
import VerifyEmail from '../VerifyEmail.js';

test('Check if VerifyEmail component renders.', () => {
  // Render VerifyEmail main component.
  const wrapper = shallow(<VerifyEmail />);
  expect(wrapper.length).toEqual(1);
});