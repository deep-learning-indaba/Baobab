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
    const value = `[{"id":1,"filename":"1.tst","rename":"lorem.tst"},{"id":2,"filename":"2.tst","rename":"ipsum.tst"}]`
    const wrapper = shallow(
      <MultiFileValue value={value} />
    );
    expect(wrapper.contains(
      <ul>
        <li>
          <a target="_blank" href={`${prefix}1.tst&rename=lorem.tst`} />
        </li>
        <li>
          <a target="_blank" href={`${prefix}2.tst&rename=ipsum.tst`} />
        </li>
      </ul>
    )).toEqual(true);
  });

});
