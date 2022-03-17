import React from "react";
import { shallow } from "enzyme";
import EventHome from "../EventHome";

test("Check if Home component renders.", () => {
  // Render Home main component.
  const wrapper = shallow(<EventHome />);
  expect(wrapper.length).toEqual(1);
});
