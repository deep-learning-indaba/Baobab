import React from "react";
import "./Style.css";



class MultiFileComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            description: "",
            file: {},
        }
    }

    handleChange = event => {
        const value = event.target.value;
        console.log(value)
        this.setState({
            description: value
        })
    };

    handleUpload = event => {
        const value = event.target.files[0];
        this.setState({
            file: value
        })

        this.props.handleUpload(value, this.state.description)
    };


    render() {
        return (

            <form className="upload-item-wrapper">
                <label>Upload File</label>
                <div className="upload-item-container">
                <input onChange={this.handleChange} placeholder="Please add a description" type="text"></input>
                <input onChange={this.handleUpload} type="file"></input>
                </div>
            </form>

        )
    }
}

export default MultiFileComponent;




