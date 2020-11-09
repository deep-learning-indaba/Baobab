import React from "react";
import { shallow } from "enzyme";
import ResponseList from "../ResponseListForm";

jest.mock('react-i18next', () => ({
    // this mock makes sure any components using the translate HoC receive the t function as a prop
    withTranslation: () => Component => {
      Component.defaultProps = { ...Component.defaultProps, t: () => "" };
      return Component;
    },
}));
  

test("Check if ResponseList Page renders.", () => {
  const wrapper = shallow(<ResponseList />);
  expect(wrapper.length).toEqual(1);
});

test("Check if Question API call is successful.",  async () => {
    const wrapper = shallow(<ResponseList />);
    await wrapper.instance().fetchQuestions();
    expect(wrapper.state().questions.length).toBeTruthy();
});

  
test("Check if Table API call is successful.",  async () => {
    const wrapper = shallow(<ResponseList />);
    await wrapper.instance().handleData();
    expect(wrapper.state().responseTable.length).toBeTruthy();
});

test("Check if tag API call is successful.",  async () => {
  const wrapper = shallow(<ResponseList />);
  await wrapper.instance().fetchTags();
  expect(wrapper.state().tags.length).toBeTruthy();
});

test("Check if React Table renders.", async () => {
    const wrapper = shallow(<ResponseList />);
    await wrapper.instance().handleData();
    expect(wrapper.find('.ReactTable').length).toEqual(1);
});

test("Check if toggleList function displays list.", () => {
  const wrapper = shallow(<ResponseList />);
  let listStatus = wrapper.state().toggleList;
   wrapper.instance().toggleList(listStatus, "tag");
  expect(wrapper.find('.tag-list.show').length).toEqual(1);
});

test("Check if Col function is succesfull.", async () => {
    const wrapper = shallow(<ResponseList />);
    await wrapper.instance().handleData();
    let columns = await wrapper.instance().generateCols();
    expect(columns.length).toBeTruthy();
});





