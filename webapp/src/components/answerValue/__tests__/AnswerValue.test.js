import React from "react";
import { shallow } from "enzyme";

import AnswerValue from "../AnswerValue";

test("Check if AnswerValue renders.", () => {
  // Render AnswerValue Component.
  const answer = {
    value: 'Lorem'
  }
  const question = {
    type: 'information'
  }
  const wrapper = shallow(
    <AnswerValue answer={answer} question={question} />
  );
  expect(wrapper.length).toEqual(1);
});
