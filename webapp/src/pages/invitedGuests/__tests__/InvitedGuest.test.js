import React from 'react';
import {shallow} from 'enzyme';
import InvitedGuest from '../InvitedGuest.js';

test('Check if InvitedGuest Page renders.', () => {
  // Render InvitedGuest Page.
  const wrapper = shallow(<InvitedGuest/>);
  expect(wrapper.length).toEqual(1);
});