import React, { Component } from "react";
import { withTranslation } from "react-i18next";
import FormGroup from "./FormGroup";
import MultiFileComponent from './MultiFileComponent';
import "./Style.css";
import _ from "lodash";


export class FormMultiFile extends React.PureComponent {
    constructor(props) {
        super(props);

        const initLength = (props.options && props.options.num_uploads) || 1;
        const initList = []
        for (let i = 0; i < initLength; i++) {
            initList.push({ id: i+1, name: null, file: null });
        }

        this.state = {
            fileList: initList,
            addError: false
        }
    }

    componentWillMount() {
        if (this.props.value) {
            this.setState({
                fileList: JSON.parse(this.props.value),
            })
        }
    }


    // add file
    addFile = () => {
        let handleList = this.state.fileList;
        // check against empty fields
        let condition = handleList.every(val => val.file);

        // variables
        let addError = condition ? false : true;


        // add item if there is no empty fields
        if (condition) {
            handleList.push({ 
                id: _.max(handleList.map(h=>h.id)) + 1, 
                name: null, 
                file: null
            });
        }

        this.setState({
            addError: addError,
            fileList: handleList
        }, () => {
            condition = true;
            addError = false
        })
    }

    del = (id) => {
        const newList = this.state.fileList.filter(h=>h.id !== id);

        // setState and Callback functions
        this.setState({
            fileList: newList
        },
            () => {
                if (this.props.onChange) {
                    const filteredList = this.state.fileList.filter(f=>f.file);
                    this.props.onChange(JSON.stringify(filteredList));
                }
            })
    }


    //handle upload
    handleUpload = (id, file, name) => {
        const handleList = this.state.fileList;
        return new Promise((resolve, reject) => {
            // Add new value
            const existing = _.find(handleList, h=>h.id === id);
            if (!existing.file) {  // New file, upload it
                if (this.props.uploadFile) {
                    this.props.uploadFile(file).then(fileId => {
                        existing.name = name;
                        existing.file = fileId;
                        this.setState({fileList: handleList}, () => {
                            if (this.props.onChange) {
                                const filteredList = this.state.fileList.filter(f=>f.file);
                                this.props.onChange(JSON.stringify(filteredList));
                            }
                            resolve(fileId);
                        });
                        // TODO: Handle errors from upload
                    })
                }
            }
            else {  // Already uploaded, update metadata
                existing.name = name;
                this.setState({fileList: handleList}, () => {
                    if (this.props.onChange) {
                        const filteredList = this.state.fileList.filter(f=>f.file);
                        this.props.onChange(JSON.stringify(filteredList));
                    }
                    resolve(existing.file);
                });
            }
        });
    }

    render() {
        const t = this.props.t

        return (
            <div>
                <FormGroup>
                    {this.state.fileList.map(val => {
                        return <MultiFileComponent className="multi-file-component"
                            handleUpload={this.handleUpload}
                            errorText={this.props.errorText}
                            addError={this.state.addError}
                            del={this.del}
                            value={val}
                            key={"file_" + val.id.toString()}
                            placeholder={this.props.placeholder}
                        />
                    })}

                    <button className="add-file-btn" onClick={(e) => this.addFile(e)}>{t("Add File")}</button>
                    <div className={this.props.errorText ? "errorText display" : "errorText"}> <p>{this.props.errorText}</p> </div>
                </FormGroup>
            </div>
        );
    }

}
export default withTranslation()(FormMultiFile);

