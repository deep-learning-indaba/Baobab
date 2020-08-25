import React from "react";
import "./Style.css";
import tick from '../../images/tick.png'
import { withTranslation } from 'react-i18next';


export class MultiFileComponent extends React.Component {
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
        })

    };

    // handle File Viewing
    onFileUpload(file, fileName) {
        return new Promise(resolve => {
            const reader = new FileReader();
            reader.onload = data => {
                this.setState({
                    file: file,
                    isSubmitted: true,
                    fileData: data.target.result
                }, () => { this.props.handleUpload(file, fileName, this.state.delete, this.state.fileData) })
                resolve(data.target.result);
            };
            reader.readAsDataURL(file);
        });
    }


    // handleUpload
    handleUpload = event => {
        const value = event.target.files[0];
        let fileName = this.state.name;

        if (!this.state.name || this.state.name == "") {
            fileName = value.name
 
        }

        this.onFileUpload(value, fileName)
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
        }, () => this.props.del(this.state.file, this.state.delete))

    }


    //Submit
    submit = event => {
        event.preventDefault()
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
                this.props.handleUpload(this.state.file, this.state.name, this.state.delete, this.state.fileData)
            })
        }
    }

    // Data Pop Up
    triggerPopUp = event => {
        event.preventDefault()
        var myWindow = window.open("", "newWindow", "width=1000,height=1000");
        myWindow.document.write(`<body style="margin: 0;">
        <iframe style="width:100vw;height:100vh;" src=${this.state.fileData }></iframe>
        </body>`)

    }

    handleInput() {
        if (!this.props.value.file) {
            return (<input className={this.props.addError && !this.state.file ? "file-input error" : "file-input"}
                onChange={this.handleUpload} type="file">
            </input>)
        }
        else {
            return (<div className="file-uploaded"><img src={tick} ></img><h6 style={{ marginLeft: "3px" }}>{this.props.value.file.name}</h6></div>)
        }
    }

    componentWillMount() {
        console.log(this.props.value)
        if (this.props.value.file) {
            this.setState({
                file: this.props.value.file,
                fileData: this.props.value.filePath
            })
        }
    }

  
    render() {
        const {
            btnSubmit,
            isSubmitted,
            name,
            file
        } = this.state;

        const t = this.props.t

        return (

            <form className="upload-item-wrapper">

                <label>{t("Upload File")}</label>

                <div className="upload-item-container">

                    <div className={btnSubmit ? "file-name enter" : "file-name"}>
                        <input className={isSubmitted  ? "input-field lock" : "input-field"
                            // || this.props.errorText ? "input-field" : "input-field alert"
                        }
                            onChange={this.handleChange}
                            placeholder={this.props.value.name ? `${this.props.value.name}` : "File Name"}
                            type="text"
                            value={name}
                        ></input>

                        <button onClick={this.submit} className={btnSubmit ? "btn-submit show" : "btn-submit"}>{t("Submit")}</button>
                        <a onClick={this.nameChange} className={isSubmitted || this.props.value.name ? "edit show" : "edit"}><i className="fas fa-edit"></i></a>
                        <a onClick={this.del} className={file ? "bin show" : "bin"}><i className="fas fa-trash"></i></a>
                        <a className="view" style={file ? { display: "block" } : { display: "none" }} onClick={this.triggerPopUp}><i className="far fa-eye"></i></a>
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

export default withTranslation(MultiFileComponent)




