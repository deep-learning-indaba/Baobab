import React from 'react';
import {shallow} from 'enzyme';
import Offer from '../Offer.js';

test('Check if Offer Page renders.', () => {
  // Render Offer Page.
  const wrapper = shallow(<Offer/>);
  expect(wrapper.length).toEqual(1);
});