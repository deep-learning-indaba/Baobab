import React from 'react';
import {shallow} from 'enzyme';
import Review from '../Review.js';

test('Check if Review Form Page renders.', () => {
  // Render Review Form Page.
  const wrapper = shallow(<Review />);
  expect(wrapper.length).toEqual(1);
});
