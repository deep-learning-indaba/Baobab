import React from 'react';
import Enzyme, { shallow } from 'enzyme';
import ResetPassword from '../ResetPassword.js';


jest.mock('react-i18next', () => ({
  // this mock makes sure any components using the translate HoC receive the t function as a prop
  withTranslation: () => Component => {
    Component.defaultProps = { ...Component.defaultProps, t: () => "" };
    return Component;
  },
}));

describe('ResetPassword render', () => {
  it("ResetPassword render", () => {
    // Render ResetPassword main component.
    const wrapper = shallow(<ResetPassword />);
    expect(wrapper.length).toEqual(1);
  })
});



