import React from 'react';
import {shallow} from 'enzyme';
import MarkDownForm from '../MarkDownForm'

describe('MarkDownEditor Tests', () => {

    it('Check if MarkDownForm Renders.', () => {
        const wrapper = shallow(<MarkDownForm  />);
      
        expect(wrapper.length).toEqual(1);
      });
      
      it('Check if MarkDownEditor Renders.', () => {
          const wrapper = shallow(<MarkDownForm  />);
        
          expect(wrapper.find('.rc-med-editor')).toBeTruthy();
        });
      

})