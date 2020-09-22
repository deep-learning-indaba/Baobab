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
    await wrapper.instance().fetchData();
    expect(wrapper.state().questions.length).toBeTruthy();
});

  
test("Check if toggleList function displays list.", async () => {
    const wrapper = shallow(<ResponseList />);
    let listStatus = wrapper.state().toggleList;
    await wrapper.instance().toggleList(listStatus);
    expect(wrapper.find('.question-list.show').length).toEqual(1);
});
  
test("Check if Table API call is successful.",  async () => {
    const wrapper = shallow(<ResponseList />);
    await wrapper.instance().handleData();
    expect(wrapper.state().responseTable.length).toBeTruthy();
});

test("Check if React Table renders.", async () => {
    const wrapper = shallow(<ResponseList />);
    await wrapper.instance().handleData();
    expect(wrapper.find('.ReactTable').length).toEqual(1);
});

test("Check if Col function is succesfull.", async () => {
    const wrapper = shallow(<ResponseList />);
    await wrapper.instance().handleData();
    let columns = await wrapper.instance().generateCol();
    expect(columns.length).toBeTruthy();
});



