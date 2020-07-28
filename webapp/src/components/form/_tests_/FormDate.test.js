import React from 'react';
import { shallow, mount } from 'enzyme';
import AppicationForm from '../../../pages/applicationForm/components/ApplicationForm';
import FormDate from '../FormDate'

describe('FormDate Componenet Tests', () => {
    it('Check if FormDate renders', () => {
        const wrapper = shallow(<FormDate />);
        expect(wrapper.length).toEqual(1);
    })

    it('Check if FormDate renders', () => {
        const wrapper = shallow(<AppicationForm />);
        expect(wrapper.length).toEqual(1);
    })

    /*
     it('loads profile', () => { 
        const wrapper = mount(<AppicationForm />);
        wrapper.setProps({ person: "something_different" });
        expect(wrapper.props().person).toEqual("something_different");
    })
    */

   

});