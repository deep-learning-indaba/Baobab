import React from 'react';
import Enzyme, { shallow, mount } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
import ResetPassword from '../ResetPassword.js';


Enzyme.configure({ adapter: new Adapter() })

test('Check if ResetPassword component renders.', () => {
  // Render ResetPassword main component.
  const wrapper = shallow(<ResetPassword />);
  expect(wrapper.length).toEqual(1);
});



