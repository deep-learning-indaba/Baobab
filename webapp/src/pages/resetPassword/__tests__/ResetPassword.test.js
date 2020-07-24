import React from 'react';
import Enzyme, { shallow } from 'enzyme';
import ConfirmPasswordResetForm from '../components/ConfirmPasswordResetForm';


describe('ResetPassword error message', () => {
  // Render ResetPassword main component.
  it('Check if ResetPassword component renders error message in UI', () => {
    const wrapper = shallow(
      <ConfirmPasswordResetForm.WrappedComponent />
    );
    wrapper.setState({ error: true });

    let errorDiv = wrapper.find(".alert");

     expect(errorDiv.text());
  })
});



