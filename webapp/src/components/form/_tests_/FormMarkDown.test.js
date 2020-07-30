import React from 'react';
import {shallow} from 'enzyme';
import FormMarkDown from '../FormMarkDown.js';

describe('FormMarkDown Component test', () => {
    it('Check if FormMarkDown component renders.', () => {
        // Render FormMarkDown.js.
        const wrapper = shallow(<FormMarkDown />);
        expect(wrapper.length).toEqual(1);
      });

      it('Check if Editor Renders', () => {
        const wrapper = shallow(<FormMarkDown />);

        expect(wrapper.find('rc-md-editor')).toBeTruthy()
      });

      it('Check if uploadImg function fires', async () => {
        const wrapper = shallow(<FormMarkDown />);

        let result = await wrapper.instance().uploadImg("value");

        expect(result).toBeTruthy()
      });
})
