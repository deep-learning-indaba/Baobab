import React, { Component } from "react";
import FormGroup from "./FormGroup";
import MultiFileComponent from './MultiFileComponent';
import "./Style.css";


class FormMultiFile extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            uploads: [{ file: 1, deleted: false }],
            fileList: [],
            addError: false
        }
    }

    // add file
    addFile = () => {
        let condition = true;
        let addError = false;
        const uploads = this.state.uploads;
        const fileList = this.state.fileList;
        let filterDelItems = uploads.filter((val, index) => {
            return val.deleted != true
        })
        console.log(filterDelItems)
        // Check uplaods array for le

        if (filterDelItems.length > fileList.length) {
            condition = false;
            addError = true
        }
        else {
            addError = false
            condition = true;
        }


        this.setState({
            uploads: condition ? uploads.concat({ file: uploads.length + 1, deleted: false }) : uploads,
            addError: addError
        }, () => console.log(this.state.addError))


    }

    //handle upload
    handleUpload = (file, name, del) => {

        // function variables
        let handleDuplicates = false;
        let handleList = this.state.fileList;
        let uploads = this.state.uploads;
        let removeFile;


        // assign data
        var newFile = { name: `${name}`, file: file }

        // handle Delete
        if (del) {
            if (uploads.length == 1) {
                uploads.concat({ file: null, deleted: true })
            }
            else {
                handleList.map(val => {
                    if (val.file == file) {
                        removeFile = handleList.indexOf(val)
                        handleList.splice(handleList.indexOf(val), 1)
                        console.log(uploads)
                        console.log(removeFile)

                    }
                })

                if (removeFile > -1) {
                    uploads[removeFile] = { file: null, deleted: true }
                }
            }

        }

        // if not delete then handle otherwise
        else {
            // test and handle updated values
            handleList.map(val => {
                if (val.file == file) {
                    handleList.splice(handleList.indexOf(val), 1, newFile)
                    handleDuplicates = true;
                }
            })

            // concat or return if file is just being updated
            if (!handleDuplicates) {
                handleList.push(newFile)
                this.props.uploadFile(file)
            }
        }

        // setState and Callback functions
        this.setState({
            fileList: handleList,
            uploads: uploads,

        },  // reset function variables
            () => {
                handleDuplicates = false;
                removeFile = null;
            })

        console.log(this.state.fileList)
        console.log(this.state.uploads)
    }


    render() {
        return (
            <div>
                <FormGroup>
                    {this.state.uploads.map((val) => {
                        if (!val.deleted)
                            return <MultiFileComponent className="multi-file-component"
                                handleUpload={(file, name, del) => this.handleUpload(file, name, del)}
                                errorText={this.props.errorText}
                                addError={this.state.addError}
                                del={(file) => this.del(file)}
                            />
                    })}

                    <button className="add-file-btn" onClick={(e) => this.addFile(e)}>Add File</button>
                    <div className={this.props.errorText ? "errorText display" : "errorText"}> <p>{this.props.errorText}</p> </div>
                </FormGroup>
            </div>
        );
    }

}
export default FormMultiFile;
