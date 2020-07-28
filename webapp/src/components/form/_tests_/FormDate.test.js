import React from 'react';
import { shallow, mount } from 'enzyme';
import AppicationForm from '../../../pages/applicationForm/components/ApplicationForm';
import FormDate from '../FormDate'

describe('FormDate Componenet Tests', () => {
    it('Check if FormDate renders', () => {
        const wrapper = shallow(<FormDate />);
        expect(wrapper.length).toEqual(1);
    })

    it('Check if AppicationFor renders', () => {
        const wrapper = shallow(<AppicationForm.WrappedComponent />);
        expect(wrapper.length).toEqual(1);
    })

     it('loads profile', async () => { 
        const wrapper = mount(<AppicationForm.WrappedComponent />);
        let result = await wrapper.instance().componentDidMount();
        expect(result).toEqual("something_different");
    })

});