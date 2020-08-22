import React from "react";
import "./Style.css";
// import edit from '../../images/edit2.png'
// import bin from '../../images/bin.png'
// import tick from '../../images/green_tick.png'


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
            btnSubmit: true
        })
    }

    // delete File
    del = event => {
        event.preventDefault()
        this.setState({
            delete: true
        }, () => this.props.handleUpload(this.state.file, this.state.name, this.state.delete, this.state.fileData))

    }


    //Submit
    submit = event => {
        event.preventDefault()
        this.setState({
            btnSubmit: false,
            isSubmitted: true
        }, () => {
            this.props.handleUpload(this.state.file, this.state.name, this.state.delete, this.state.fileData)
        })
    }

    // Data Pop Up
    triggerPopUp = event => {
        event.preventDefault()
        var myWindow = window.open("", "newWindow", "width=1000,height=1000");
        myWindow.document.write(`<body style="margin: 0;">
        <iframe style="width:100vw;height:100vh;" src=${this.state.fileData}></iframe>
        </body>`)

        //window.open('url','name','specs');
    }

    handleInput() {
        if (!this.props.value.file) {
            return (<input className={this.props.addError && !this.state.file ? "file-input error" : "file-input"}
                onChange={this.handleUpload} type="file">
            </input>)
        }
        else {
            return (<div className="file-uploaded"><img ></img><h6 style={{marginLeft: "3px"}}>{this.props.value.name}</h6></div>)
        }
    }

    componentWillMount() {
        if (this.props.value.file) {
            this.setState({
                file: this.props.value.file
            })
        }
    }



    render() {
        console.log("rendered")
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

                    <div className={btnSubmit ? "file-name enter" : "file-name"}>
                        <input className={isSubmitted ? "input-field lock" : "input-field"
                            // || this.props.errorText ? "input-field" : "input-field alert"
                        }
                            onChange={this.handleChange}
                            placeholder={this.props.value.name ? `${this.props.value.name}` : "File Name"}
                            type="text"
                            value={name}
                        ></input>

                        <button onClick={this.submit} className={btnSubmit ? "btn-submit show" : "btn-submit"}>Submit</button>
                        <a onClick={this.nameChange} className={isSubmitted ? "edit show" : "edit"}><img  /></a>
                        <a><img onClick={this.del} className={file ? "bin show" : "bin"}  /></a>
                        <a style={file ? { display: "block" } : { display: "none" }} onClick={this.triggerPopUp}>View File</a>
                    </div>

                    <div className={file ? "file-input-wrapper lock" : "file-input-wrapper"}>
                        {this.handleInput()}
                    </div>
                </div>

            </form>

        )
    }
}

export default MultiFileComponent;




