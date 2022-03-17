import React from "react";
import { shallow } from "enzyme";
import ProfileList from "../ProfileList";

test("Checking if ProfileList component renders", () => {
  //Rendering the ProfileList component
  const wrapper = shallow(<ProfileList />);
  expect(wrapper.length).toEqual(1);
});
