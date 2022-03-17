import React from "react";
import { shallow, mount } from "enzyme";
import FormDate from "../FormDate";

describe("FormDate Componenet Tests", () => {
  it("Check if FormDate renders", () => {
    const wrapper = shallow(<FormDate />);
    expect(wrapper.length).toEqual(1);
  });

  it("Check if FormDate renders error in IU", () => {
    const wrapper = shallow(<FormDate />);

    wrapper.setProps({ id: "123", errorText: "There is an error" });
    expect(wrapper.exists(".react-datetime-picker.error")).toEqual(true);
  });
});
