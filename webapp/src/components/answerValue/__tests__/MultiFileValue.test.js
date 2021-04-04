import React from "react";
import { shallow } from "enzyme";

import MultiFileValue from "../MultiFileValue";

const prefix = process.env.REACT_APP_API_URL + "/api/v1/file?filename=";

describe('MultiFileValue Tests', () => {

  it('Renders MultiFileValue component.', () => {
    const value = `[{"id":1,"file":"1.tst","name":"lorem.tst"},{"id":2,"file":"2.tst","name":"ipsum.tst"}]`
    const wrapper = shallow(
      <MultiFileValue value={value} />
    );
    expect(wrapper.length).toEqual(1);
  });

  it('Renders list of files.', () => {
    const value = `[{"id":1,"file":"1.tst","name":"lorem.tst"},{"id":2,"file":"2.tst","name":"ipsum.tst"}]`
    const wrapper = shallow(
      <MultiFileValue value={value} />
    );
    expect(wrapper.contains(
      <ul>
        <li key="1">
          <a target="_blank" href={`${prefix}1.tst`}>
            lorem.tst
          </a>
        </li>
        <li key="2">
          <a target="_blank" href={`${prefix}2.tst`}>
            ipsum.tst
          </a>
        </li>
      </ul>
    )).toEqual(true);
  });

});
