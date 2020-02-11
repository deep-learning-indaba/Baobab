import React from "react";
import { shallow } from "enzyme";
import EventConfig from "../EventConfig";

test("Check if EventConfig component renders.", () => {
  // Render EventConfig main component.
  const wrapper = shallow(<EventConfig />);
  expect(wrapper.length).toEqual(1);
});
