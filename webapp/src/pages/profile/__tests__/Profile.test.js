import React from "react";
import { shallow } from "enzyme";
import Profile from "../Profile.js";

test("Check if Profile Page renders.", () => {
  // Render Profile Page.
  const wrapper = shallow(<Profile />);
  expect(wrapper.length).toEqual(1);
});
