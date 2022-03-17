import React from "react";
import { shallow } from "enzyme";
import ResponsePage from "./ResponsePage";
import { applicationFormService } from "../../services/applicationForm/applicationForm.service";
import { responsesService } from "../../services/responses/responses.service";

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

/* The form data API call requires Authentication and therefore we need to insert formData manualy */
const formData = {
  sections: [
    {
      depends_on_question_id: null,
      description:
        "This is the official application form to apply for participation in the Deep Learning Indaba to be held 25-31 August 2019 in Nairobi, Kenya. Students can also use this application form to apply for travel and accommodation awards. \n \n \n Closing date: 30 April 2019",
      id: 12,
      name: "Indaba 2019 Application Form",
      order: 1,
      questions: [],
      show_for_values: false,
    },
    {
      depends_on_question_id: null,
      description:
        "This is the official application form to apply for participation in the Deep Learning Indaba to be held 25-31 August 2019 in Nairobi, Kenya. Students can also use this application form to apply for travel and accommodation awards. \n \n \n Closing date: 30 April 2019",
      id: 12,
      name: "Indaba 2019 Application Form",
      order: 1,
      questions: [],
      show_for_values: false,
    },
  ],
};

const reviewersData = [
  {
    reviewer_user_id: 1,
    user_title: "Mr",
    firstname: "Joe",
    lastname: "Bloggs",
    status: "completed",
  },
  {
    reviewer_user_id: 2,
    user_title: "Ms",
    firstname: "Jane",
    lastname: "Bloggs",
    status: "started",
  },
];

const applicationData = {
  id: 1,
  application_form_id: 1,
  user_id: 1,
  is_submitted: false,
  submitted_timestamp: null,
  is_withdrawn: false,
  withdrawn_timestamp: null,
  started_timestamp: "2020-01-01",
  answers: [],
  language: "en",
  user_title: "Mx",
  firstname: "Finn",
  lastname: "Dog",
  tags: [],
  reviewers: [],
};

// Tests
test("Check if Response Page renders.", () => {
  const wrapper = shallow(<ResponsePage {...props} />);
  expect(wrapper.length).toEqual(1);
});

test("Check if Question and Answer html renders.", async () => {
  const wrapper = shallow(<ResponsePage {...props} />);
  wrapper.setState({
    applicationForm: formData,
    reviewers: reviewersData,
    applicationData: applicationData,
    isLoading: false,
  });
  expect(wrapper.find(".Q-A").length).toBeTruthy();
});

test("Check if tag list renders.", async () => {
  const wrapper = shallow(<ResponsePage {...props} />);
  wrapper.setState({
    isLoading: false,
    applicationData: applicationData,
    reviewers: reviewersData,
    tagMenu: true,
    tagList: [{ headline: "" }, { headline: "" }],
    eventLanguages: ["En", "Fr"],
  });
  expect(wrapper.find(".tag-response.show").length).toEqual(1);
});
