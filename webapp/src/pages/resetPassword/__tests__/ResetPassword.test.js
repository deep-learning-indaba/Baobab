import React from "react";
import Enzyme, { shallow } from "enzyme";
import ResetPassword from "../ResetPassword.js";
import ConfirmPasswordResetForm from "../components/ConfirmPasswordResetForm";

jest.mock("react-i18next", () => ({
  // this mock makes sure any components using the translate HoC receive the t function as a prop
  withTranslation: () => (Component) => {
    Component.defaultProps = { ...Component.defaultProps, t: () => "" };
    return Component;
  },
}));

describe("ResetPassword render", () => {
  it("ResetPassword render", () => {
    // Render ResetPassword main component.
    const wrapper = shallow(<ResetPassword />);
    expect(wrapper.length).toEqual(1);
  });
});

describe("ResetPassword error message", () => {
  it("Check if ResetPassword component renders error message in UI", async () => {
    const wrapper = shallow(<ConfirmPasswordResetForm.WrappedComponent />);

    wrapper.setState({ password: "123", token: "123" });

    const event = { preventDefault: () => {} };

    var response = await wrapper.instance().handleSubmit(event);

    expect(response.length > 0).toEqual(true);
    expect(wrapper.state().error.length > 0).toEqual(true);
    expect(wrapper.find(".alert").text().length > 0).toEqual(true);
  });
});
