import React from "react";
import { shallow } from "enzyme";
import ResponsePage from "./ResponsePage";

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

/* The form data API call requires Authentication and therefore we need to insert formData manualy */
const formData = {
    sections: [
        {
        depends_on_question_id: null,
        description: "This is the official application form to apply for participation in the Deep Learning Indaba to be held 25-31 August 2019 in Nairobi, Kenya. Students can also use this application form to apply for travel and accommodation awards. \n \n \n Closing date: 30 April 2019",
        id: 12,
        name: "Indaba 2019 Application Form",
        order: 1,
        questions: [],
        show_for_values: false
        }
    ]
}

// Tests
test("Check if Response Page renders.", () => {
    const wrapper = shallow(<ResponsePage {...props} />);
    expect(wrapper.length).toEqual(1);
});

test("Check if API Data call is successful.", async () => {
    const wrapper = shallow(<ResponsePage {...props} />);
    await wrapper.instance().fetchData();
    expect(wrapper.state().applicationData.id).toBeTruthy();
});

test("Check if Question and Answerer html renders.", async () => {
    const wrapper = shallow(<ResponsePage {...props} />);
    await wrapper.instance().fetchData();
    wrapper.setState({ applicationForm: formData })
    expect(wrapper.find('.Q-A').length).toEqual(1);
});

test("Check if tag list renders.", async () => {
    const wrapper = shallow(<ResponsePage {...props} />);
    await wrapper.instance().fetchTags();
    wrapper.setState({tagMenu: true})
    expect(wrapper.find('.tag-response.show').length).toEqual(1);
});

test("Check if Tag API updates state.", async () => {
    const wrapper = shallow(<ResponsePage {...props} />);
    let prevState = wrapper.state().applicationData;
    await wrapper.instance().postResponseTag({
        "tag_id": 1,
        "response_id": 2,
        "event_id": 3
    });
    expect(wrapper.state().applicationData != prevState).toBeTruthy();
});




