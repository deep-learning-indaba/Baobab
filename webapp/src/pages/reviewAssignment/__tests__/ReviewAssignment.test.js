import React from 'react';
import { shallow } from 'enzyme';
import EventStats from '../ReviewAssignment';

test('Check if ReviewAssignment component renders.', () => {
  // Render EventStats main component.
  const wrapper = shallow(<ReviewAssignment />);
  expect(wrapper.length).toEqual(1);
});