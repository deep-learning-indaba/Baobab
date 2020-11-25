import React from "react";
import { shallow } from "enzyme";
import { eventService } from "../../../services/events/events.service";
import { EventConfigComponent } from "../components/EventConfigComponent";


jest.mock('react-i18next', () => ({
  // this mock makes sure any components using the translate HoC receive the t function as a prop
  withTranslation: () => Component => {
    Component.defaultProps = { ...Component.defaultProps, t: () => "" };
    return Component;
  },
}));

describe("EventConfigComponent Tests", () => {

  let wrapper;

  beforeEach(() => {
    wrapper = shallow(<EventConfigComponent />);
  });


  it("Check if EventConfig component renders.", () => {
    // Render EventConfig main component.
    expect(wrapper.length).toEqual(1);
  });

  it("Check if eventService API calls occur", async () => {
    const result = await eventService.getEvent(1);
    expect(result.error).toBeTruthy()
  });


  it("Check if function onClickCancel works.", () => {
    wrapper.instance().onClickCancel();
    expect(wrapper.state().hasBeenUpdated).toEqual(false);
  });


  it("Check if function updateEventDetails works.", () => {

    let e = { target: { value: "test" } };

    let prevState = wrapper.state().hasBeenUpdated;

    wrapper.instance().updateEventDetails("test", e);
    expect(wrapper.state().hasBeenUpdated !== prevState).toBeTruthy();
  });
})





