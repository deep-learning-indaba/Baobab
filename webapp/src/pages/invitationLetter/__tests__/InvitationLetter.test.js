import React from "react";
import { shallow } from "enzyme";
import InvitationLetter from "../index.js";

test("Check if Home component renders.", () => {
  // Render Invitation Letter component.
  const wrapper = shallow(<InvitationLetter />);
  expect(wrapper.length).toEqual(1);
});
