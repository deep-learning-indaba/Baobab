import React from "react";
import { shallow } from "enzyme";
import App from "../App.js";

test("Check if App component renders.", () => {
  // Render App.js main component.
  const wrapper = shallow(<App />);
  expect(wrapper.length).toEqual(1);
});
