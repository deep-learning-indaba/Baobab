import React from "react";
import "./Style.css";



class UploadFileItem extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            description: "",
            file: {},
        }
    }

    handleChange = event => {
        const value = event && event.target ? event.target.value : event;
        console.log(value)
        this.setState({
            description: value
        })
      };

      handleUpload = event => {
        const value = event && event.target ? event.target.value : event;
        console.log(value)
        this.setState({
            file: value
        })
      };
      

    render() {
        return (

            <form className="upload-item-wrapper">
                <label>Upload File</label>
                <input onChange={this.handleChange} placeHolder="Please add a description" type="text"></input>
                <input onChange={this.handleUpload}  type="file"></input>
            </form>

        )
    }
}

export default UploadFileItem;




