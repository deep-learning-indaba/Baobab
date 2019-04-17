import React from "react";
import { shallow } from "enzyme";
import ReviewHistory from "../ReviewHistory.js/index.js";

test("Check if Review History Page renders.", () => {
  // Render ReviewHistory Form Page.
  const wrapper = shallow(<ReviewHistory />);
  expect(wrapper.length).toEqual(1);
});
