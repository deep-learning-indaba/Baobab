import React from "react";
import { shallow } from "enzyme";
import CreateAccount from "../CreateAccount.js";
import PassStrength from "../components/PassStrength";

test("Check if CreateAccount Page renders.", () => {
  // Render CreateAccount Page.
  const wrapper = shallow(<CreateAccount />);
  expect(wrapper.length).toEqual(1);
});

test("Check if PassStrength component renders.", () => {
  // Render CreateAccount Page.
  const wrapper = shallow(<PassStrength />);
  expect(wrapper.length).toEqual(1);
});
