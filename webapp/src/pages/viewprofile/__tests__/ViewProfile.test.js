import React from "react";
import { shallow } from "enzyme";
import ViewProfile from "../ViewProfile";

test("Check if ViewProfile component renders.", () => {
  //rendering the ViewProfile component
  const wrapper = shallow(<ViewProfile />);
  expect(wrapper.length).toEqual(1);
});
