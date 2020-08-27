
import React from "react"
import { shallow, mount } from 'enzyme';
import FormMultiFile from '../FormMultiFile.js';


jest.mock('react-i18next', () => ({
    // this mock makes sure any components using the translate HoC receive the t function as a prop
    withTranslation: () => Component => {
        Component.defaultProps = { ...Component.defaultProps, t: () => "" };
        return Component;
    },
}));

const onSubmitSpy = jest.fn();
const uploadFile = onSubmitSpy;

//  FormMultiFile and  Tests
describe('FormMultiFile Tests', () => {
    it('Check if FormMultiFile Page renders.', () => {
        const wrapper = shallow(<FormMultiFile />);
        expect(wrapper.length).toEqual(1);
    });

    it('Check if FormMultiFile state updates in rendered().', () => {
        const wrapper = shallow(<FormMultiFile />);
        wrapper.setState({ fileList: [{ id: 1, name: null, file: null }, { id: 2, name: null, file: null }] });
        expect(wrapper.find('.multi-file-component').length).toEqual(2);
    });


    it('Check if FormMultiFile adds upload components render().', () => {
        const wrapper = shallow(<FormMultiFile />);
        wrapper.setState({ fileList: [{ id: 1, name: "test", file: "test" }, { id: 2, name: "test", file: "test" }] });
        wrapper.instance().addFile();
        expect(wrapper.find('.multi-file-component').length).toEqual(2);
    });


    it('Check if FormMultiFile adds components in render() when props change.', () => {
        const wrapper = shallow(<FormMultiFile uploadFile={uploadFile} />);
        wrapper.setState({ fileList: [{ id: 1, name: "test", file: "test" }, { id: 2, name: "test", file: "test" }] });
        wrapper.instance().handleUpload();
        expect(wrapper.find('.multi-file-component').length).toEqual(2);
    });

})











