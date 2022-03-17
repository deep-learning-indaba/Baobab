import React from "react";
import { shallow } from "enzyme";
import EventStats from "../EventStats";

test("Check if EventStats component renders.", () => {
  // Render EventStats main component.
  const wrapper = shallow(<EventStats />);
  expect(wrapper.length).toEqual(1);
});
