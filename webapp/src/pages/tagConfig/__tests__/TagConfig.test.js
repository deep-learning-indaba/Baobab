import React from "react";
import { shallow } from "enzyme";
import TagConfig from "../TagConfig";

test("Check if TagConfig component renders.", () => {
  // Render EventConfig main component.
  const wrapper = shallow(<TagConfig />);
  expect(wrapper.length).toEqual(1);
});
