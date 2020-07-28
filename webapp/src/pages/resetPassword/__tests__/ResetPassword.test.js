import React from 'react';
import Enzyme, { shallow } from 'enzyme';
import ResetPassword from '../ResetPassword.js';


describe('ResetPassword render', () => {
  it("ResetPassword render", () => {
    // Render ResetPassword main component.
    const wrapper = shallow(<ResetPassword />);
    expect(wrapper.length).toEqual(1);
  })
});



