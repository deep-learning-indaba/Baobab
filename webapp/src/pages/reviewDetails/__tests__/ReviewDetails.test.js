import React from "react";
import { shallow } from "enzyme";
import ReviewDetailsPage from "../";
import { reviewService } from "../../../services/reviews/review.service";

jest.mock('react-i18next', () => ({
  // this mock makes sure any components using the translate HoC receive the t function as a prop
  withTranslation: () => Component => {
    Component.defaultProps = { ...Component.defaultProps, t: () => "" };
    return Component;
  },
}));

// Mock Props
const props = {
  event: {
    id: 3
  },
  match: {
    params: {
      id: 1,
      eventKey: "1234"
    }
  }
}

test("Check if Review Details Page renders.", () => {
  const wrapper = shallow(<ReviewDetailsPage {...props} />);
  expect(wrapper.length).toEqual(1);
});

/*
todo: Uncomment after API has been merged 
test("Check if reviewService API call works.", async () => {
  const response = await reviewService.getReviewDetails(props.event.id, false, []);
  expect(response.error).toBeTruthy();
});
*/
