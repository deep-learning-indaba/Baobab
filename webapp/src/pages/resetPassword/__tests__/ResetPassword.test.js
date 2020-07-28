import React from 'react';
import Enzyme, { shallow } from 'enzyme';
import ConfirmPasswordResetForm from '../components/ConfirmPasswordResetForm';
import ResetPassword from '../ResetPassword.js';


describe('ResetPassword render', () => {
  it("ResetPassword render", () => {
    // Render ResetPassword main component.
    const wrapper = shallow(<ResetPassword />);
    expect(wrapper.length).toEqual(1);
  })
});


describe('ResetPassword error message', () => {
  it('Check if ResetPassword component renders error message in UI', () => {
    const wrapper = shallow(
      <ConfirmPasswordResetForm.WrappedComponent />
    );
    wrapper.setState({ error: true });

    let errorDiv = wrapper.find(".alert");

    expect(errorDiv.text());
  })
});



