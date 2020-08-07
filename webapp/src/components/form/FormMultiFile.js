import React, { Component } from "react";
import FormGroup from "./FormGroup";
import MultiFileComponent from './MultiFileComponent';
import "./Style.css";


class FormMultiFile extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            uploads: [1],
            fileList: []
        }
    }

    addFile() {
        this.setState({
            uploads: this.state.uploads.concat(1)
        })

    }

    handleUpload(file, description) {
        var newFile = { name: `${file}`, file: file, description: description }

        this.setState({
            fileList: this.state.fileList.concat(newFile)
        }, () => this.props.uploadFile(file)) 

    }


    render() {
        return (
            <div>
                <FormGroup>
                    {this.state.uploads.map((val) => {
                        return <MultiFileComponent
                            handleUpload={(file, description) => this.handleUpload(file, description)}
                        />
                    })}

                    <button className="add-file-btn" onClick={(e) => this.addFile(e)}>+</button>
                </FormGroup>
            </div>
        );
    }
}
export default FormMultiFile;
