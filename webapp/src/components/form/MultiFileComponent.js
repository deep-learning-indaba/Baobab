import React from "react";
import "./Style.css";
import edit from '../../images/edit2.png'
import bin from '../../images/bin.png'


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
        })

    };

    // handleUpload
    handleUpload = event => {
        const value = event.target.files[0];
        let fileName = this.state.name;

        if (!this.state.name || this.state.name == "") {
            fileName = value.name
        }

        this.setState({
            file: value,
            isSubmitted: true,
        }, () => { this.props.handleUpload(value, fileName, this.state.delete) })
    };

    // Name Change
    nameChange = event => {
        event.preventDefault()
        this.setState({
            isSubmitted: false,
            name: "",
            btnSubmit: true
        })
    }

    // delete File
    del = event => {
        event.preventDefault()
        this.setState({
            delete: true
        }, () => this.props.handleUpload(this.state.file, this.state.name, this.state.delete))

    }


    //Submit
    submit = event => {
        event.preventDefault()
        this.setState({
            btnSubmit: false,
            isSubmitted: true
        }, () => {
            this.props.handleUpload(this.state.file, this.state.name, this.state.delete)
        })
    }



    render() {
        const {
            btnSubmit,
            isSubmitted,
            name,
            errorText,
            file
        } = this.state;
        return (

            <form className="upload-item-wrapper">

                <label>Upload File</label>

                <div className="upload-item-container">

                    <div className={btnSubmit ? "file-name enter" : "file-name" }>
                        <input className={isSubmitted ? "input-field lock" : "input-field"
                            // || this.props.errorText ? "input-field" : "input-field alert"
                        }
                            onChange={this.handleChange}
                            placeholder="File Name"
                            type="text"
                            value={name}
                        ></input>

                        <button onClick={this.submit} className={btnSubmit ? "btn-submit show" : "btn-submit"}>Submit</button>
                        <a onClick={this.nameChange} className={isSubmitted ? "edit show" : "edit"}><img src={edit} /></a>
                        <a><img onClick={this.del} className={file ? "bin show" : "bin"} src={bin} /></a>
                        <a href={this.state.file}>View File</a>
                    </div>

                    <div className={file ? "file-input-wrapper lock" : "file-input-wrapper"}>
                        <input className={this.props.addError && !file ? "file-input error" : "file-input"} onChange={this.handleUpload} type="file"></input>
                    </div>


                </div>
            </form>

        )
    }
}

export default MultiFileComponent;




