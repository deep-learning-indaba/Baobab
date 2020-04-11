import React from 'react';
import { shallow } from 'enzyme';
import Reference from '../Reference';

test('Checking if Reference component renders', () => {
    //Rendering the Reference component
    const wrapper = shallow(<Reference />);
    expect(wrapper.length).toEqual(1);
})