import React, { Component } from "react";
import FormGroup from "./FormGroup";
import UploadFileItem from './UploadFileItem';
import "./Style.css";


class FormMultiFile extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            files: ['1']
        }
    }

    addFile() {
        var oldVal = this.state.files;
        var newVal = oldVal.push('1')
        this.setState({
            file: newVal
        })
    }


    render() {
        return (
            <div>
                <FormGroup>
                    {this.state.files.map((val) => {
                        return <UploadFileItem 
                    />
                    })}

                    <button onClick={(e) => this.addFile(e)}>+</button>
                </FormGroup>
            </div>
        );
    }
}
export default FormMultiFile;
