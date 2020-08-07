import React from 'react';
import Enzyme, { shallow } from 'enzyme';
import MultiFileComponent from '../MultiFileComponent'
import FormMultiFile from '../FormMultiFile'


describe('MultiFileComponent Tests', () => {

    it('Check if component renders', () => {
        const wrapper = shallow(<MultiFileComponent />);
        expect(wrapper.length).toEqual(1);
    })

    it('Check if discription inputs changes the state', () => {
        const wrapper = shallow(<MultiFileComponent />);

        const event = {
            target: {value: 'This is just for test'}
        }

    wrapper.find('.description').simulate('change', event);
    expect(wrapper.state().description).toEqual('This is just for test')
    })
});

describe('FormMultiFile Tests', () => {

    it('Check if component renders', () => {
        const wrapper = shallow(<FormMultiFile />);
        expect(wrapper.length).toEqual(1);
    })

   it('Check if adding inputs work', () => {
    const wrapper = shallow(<FormMultiFile />);
    var initalInputs = wrapper.find('.multi-file-component').length

    wrapper.instance().addFile();
    expect(wrapper.find('.multi-file-component').length > initalInputs).toEqual(true)
})
});


