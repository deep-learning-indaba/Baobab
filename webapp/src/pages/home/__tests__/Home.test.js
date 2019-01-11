import React from 'react';
import {shallow} from 'enzyme';
import Home from '../Home.js';

test('Check if Home component renders.', () => {
  // Render Home main component.
  const wrapper = shallow(<Home />);
  expect(wrapper.length).toEqual(1);
});