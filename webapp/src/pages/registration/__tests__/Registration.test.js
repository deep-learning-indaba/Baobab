import React from "react";
import { shallow } from "enzyme";
import Registration from "../Registration";

test("Check if Registration component renders.", () => {
  // Render Registration component.
  const wrapper = shallow(<Registration />);
  expect(wrapper.length).toEqual(1);
});
