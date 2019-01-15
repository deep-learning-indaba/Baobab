import React from 'react';
import {shallow} from 'enzyme';
import Login from '../Login.js';

test('Check if Login Page renders.', () => {
  // Render Login Page.
  const wrapper = shallow(<Login />);
  expect(wrapper.length).toEqual(1);
});