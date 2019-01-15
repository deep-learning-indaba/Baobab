import React from 'react';
import {shallow} from 'enzyme';
import CreateAccount from '../CreateAccount.js';

test('Check if CreateAccount Page renders.', () => {
  // Render CreateAccount Page.
  const wrapper = shallow(<CreateAccount />);
  expect(wrapper.length).toEqual(1);
});