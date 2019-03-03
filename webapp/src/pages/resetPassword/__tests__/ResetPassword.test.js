import React from 'react';
import { shallow } from 'enzyme';
import ResetPassword from '../ResetPassword.js';

test('Check if ResetPassword component renders.', () => {
  // Render ResetPassword main component.
  const wrapper = shallow(<ResetPassword />);
  expect(wrapper.length).toEqual(1);
});