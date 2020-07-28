import React from 'react';
import { shallow } from 'enzyme';
import AppicationForm from '../../../pages/applicationForm/components/ApplicationForm'

describe('FormDate Componenet Tests', () => {
    it('Check if FormDate receives and displays error', () => {

        const wrapper = shallow(<AppicationForm />);
        expect(wrapper.length).toEqual(1);

    })

});