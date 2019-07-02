import React from 'react';
import {shallow} from 'enzyme';
import RegistrationAdmin from '../RegistrationAdmin.js';

test('Check if RegistrationAdmin Page renders.', () => {
  // Render RegistrationAdmin Page.
  const wrapper = shallow(<RegistrationAdmin/>);
  expect(wrapper.length).toEqual(1);
});