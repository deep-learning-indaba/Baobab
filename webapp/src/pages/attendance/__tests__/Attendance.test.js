import React from "react";
import { shallow } from "enzyme";
import Attendance from "../Attendance";

test("Check if Attendance Page renders.", () => {
  // Render Attendance Page.
  const wrapper = shallow(<Attendance />);
  expect(wrapper.length).toEqual(1);
});
