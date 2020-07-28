import React from 'react';
import {shallow, mount} from 'enzyme';
import Application from '../Application.js';
import ApplicationForm from '../components/ApplicationForm';
import FormDate from '../../../components/form/FormDate';

test('Check if Application Form Page renders.', () => {
  // Render Application Form Page.
  const wrapper = shallow(<Application />);
  expect(wrapper.length).toEqual(1);
});

describe('Check if validate failure renders error in FormDate component UI', () => {
  it('FormDate error', () => {

  const wrapper = shallow(<FormDate />);

  wrapper.setProps({ errorText: "error"})

  expect(wrapper.props().errorText).toEqual("error")
});

})

/*
  setImmediate(() => {
    wrapper.update();
    expect(wrapper.state().errorMessage).toEqual("error")
});
*/
