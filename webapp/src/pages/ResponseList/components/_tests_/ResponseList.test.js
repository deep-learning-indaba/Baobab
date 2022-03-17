import React from "react";
import { shallow, mount } from "enzyme";
import ResponseList from "../ResponseListForm";
import { applicationFormService } from "../../../../services/applicationForm/applicationForm.service";
import { responsesService } from "../../../../services/responses/responses.service";
import { tagsService } from "../../../../services/tags/tags.service";

jest.mock("react-i18next", () => ({
  // this mock makes sure any components using the translate HoC receive the t function as a prop
  withTranslation: () => (Component) => {
    Component.defaultProps = { ...Component.defaultProps, t: () => "" };
    return Component;
  },
}));

// Mock Props
const props = {
  event: {
    id: 3,
  },
  match: {
    params: {
      id: 1,
      eventKey: "1234",
    },
  },
};

const mockData = [
  {
    response_id: 1,
    user_title: "Mr",
    firstname: "Jimmy",
    lastname: "Fallon",
    start_date: "2020-06-01 [...]", // ISO8601 format
    is_submitted: true,
    is_withdrawn: false,
    submitted_date: "2020-06-03 [...]", // ISO8601 format
    language: "en",
    answers: [
      {
        question_id: 3,
        value: "Hello world",
        type: "short-text",
        options: null,
      },
      {
        question_id: 5,
        value: "harry-potter",
        "multi-choice": null,
        options: [
          { label: "Harry Potter", value: "harry-potter" },
          { label: "X-men", value: "x-men" },
        ],
      },
    ],
    tags: [
      //  <-------- NEW
      { id: 5, name: "Education" },
      { id: 7, name: "Healthcare" },
    ],
  },
  {
    response_id: 2,
    user_title: "Ms",
    firstname: "Halle",
    lastname: "Berry",
    start_date: "2020-06-01 [...]", // ISO8601 format
    is_submitted: true,
    is_withdrawn: false,
    submitted_date: "2020-06-03 [...]", // ISO8601 format
    language: "en",
    answers: [
      {
        question_id: 3,
        value: "Hello world",
        type: "short-text",
        options: null,
      },
      {
        question_id: 5,
        value: "x-men",
        "multi-choice": null,
        options: [
          { label: "Harry Potter", value: "harry-potter" },
          { label: "X-men", value: "x-men" },
        ],
      },
    ],
    tags: [
      //  <-------- NEW
      { id: 2, name: "Desk Reject" },
      { id: 7, name: "Healthcare" },
    ],
  },
];

test("Check if ResponseList Page renders.", () => {
  const wrapper = shallow(<ResponseList {...props} />);
  expect(wrapper.length).toEqual(1);
});

test("Check if Question API call works.", async () => {
  const response = await applicationFormService.getQuestionList(props.event.id);
  expect(response.error).toBeTruthy();
});

test("Check if responsesService API call works.", async () => {
  const response = await responsesService.getResponseList(
    props.event.id,
    false,
    []
  );
  expect(response.error).toBeTruthy();
});

test("Check if tag API call is successful.", async () => {
  const response = await tagsService.getTagList(props.event.id);
  expect(response.error).toBeTruthy();
});

test("Check if React Table renders.", async () => {
  const wrapper = shallow(<ResponseList {...props} />);
  wrapper.setState({
    toggleList: null,
    isLoading: false,
  });
  expect(wrapper.find(".ReactTable").length).toEqual(1);
});

test("Check if toggleList function displays list.", () => {
  const wrapper = shallow(<ResponseList {...props} />);
  let listStatus = wrapper.state().toggleList;
  wrapper.setState({
    isLoading: false,
  });
  wrapper.instance().toggleList(listStatus, "tag");
  expect(wrapper.find(".tag-list.show").length).toEqual(1);
});

test("Check if Col function is succesfull.", async () => {
  const wrapper = shallow(<ResponseList {...props} />);
  wrapper.setState({
    responseTable: mockData,
  });
  let columns = await wrapper.instance().generateCols();
  expect(columns.length).toBeTruthy();
});
