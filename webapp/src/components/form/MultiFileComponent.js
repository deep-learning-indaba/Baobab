import React from "react";
import "./Style.css";
import tick from '../../images/tick.png'
import { withTranslation } from 'react-i18next';

const baseUrl = process.env.REACT_APP_API_URL;

 class MultiFileComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            delete: false,
            btnSubmit: false,
            isSubmitted: false,
            name: null,
            file: null,
        }
    }

    // handleChange
    handleChange = event => {
        const value = event.target.value;

        this.setState({
            name: value
        });

    };

    // handleUpload
    handleUpload = event => {
        const value = event.target.files[0];
        let fileName = this.state.name;

        if (!this.state.name || this.state.name == "") {
            fileName = value.name
        }

        if (this.props.handleUpload) {
            this.props.handleUpload(this.props.value.id, value, fileName).then(() => {
                this.setState({
                    isSubmitted: true
                });
            });
        }
    };

    // Name Change
    nameChange = event => {
        event.preventDefault()
        this.setState({
            isSubmitted: false,
            name: "",
            btnSubmit: true,
            prevName: event.target.value
        })
    }

    // delete File
    del = event => {
        event.preventDefault()
  
        this.setState({
            delete: true
        }, () => this.props.del(this.props.value.id))

    }


    //Submit
    submit = event => {
        event.preventDefault();
        if(!this.state.name.length) {
            this.setState({
                error: true
            })
        }
        else {
            this.setState({
                btnSubmit: false,
                isSubmitted: true,
                error: false
            }, () => {
                this.props.handleUpload(this.props.value.id, this.props.value.file, this.state.name)
            })
        }
    }

    handleInput() {
        if (!this.props.value.file) {
            return (<input className={this.props.addError && !this.props.value.file ? "file-input error" : "file-input"}
                onChange={this.handleUpload} type="file">
            </input>)
        }
        else {
            return (<div className="file-uploaded"><img src={tick} ></img><h6 style={{ marginLeft: "3px" }}>{this.props.value.file.name}</h6></div>)
        }
    }

    render() {
        const {
            btnSubmit,
            isSubmitted,
            name
        } = this.state;

        const file = this.props.value.file;

        const t = this.props.t

        return (

            <form className="upload-item-wrapper">

                <label>{t("Upload File")}</label>

                <div className="upload-item-container">

                    <div className={btnSubmit ? "file-name enter" : "file-name"}>
                        <input className={isSubmitted  ? "input-field lock" : "input-field"}
                            onChange={this.handleChange}
                            placeholder={this.props.value.name ? `${this.props.value.name}` : t("Enter File Name")}
                            type="text"
                            value={name}
                        ></input>

                        <button onClick={this.submit} className={btnSubmit ? "btn-submit show" : "btn-submit"}>{t("Submit")}</button>
                        <a onClick={this.nameChange} className={isSubmitted || this.props.value.name ? "edit show" : "edit"}><i className="fas fa-edit"></i></a>
                        <a onClick={this.del} className={file ? "bin show" : "bin"}><i className="fas fa-trash"></i></a>
                        <a className="view" style={file ? { display: "block" } : { display: "none" }} href={baseUrl + "/api/v1/file?filename=" + file} target="_blank"><i className="far fa-eye"></i></a>
                    </div>
                    {this.state.error && <p style={{color: "red"}}>{t("Please enter a name")}</p>}

                    <div className={file ? "file-input-wrapper lock" : "file-input-wrapper"}>
                        {this.handleInput()}
                    </div>
                </div>

            </form>

        )
    }
}

export default withTranslation()(MultiFileComponent)




