import React, { Component } from "react";
import { withRouter } from "react-router";

const baseUrl = process.env.REACT_APP_API_URL;

class ViewFile extends Component {
  
    constructor(props) {
        super(props);
        this.state = {
            fileLocation: null
        }
    }

    componentDidMount() {
        if (this.props.match && this.props.match.params) {
            const filename = this.props.match.params.filename;
            const fileLocation = baseUrl + "/api/v1/file?filename=" + filename;
            this.setState({
                fileLocation: fileLocation
            });
            window.location = fileLocation;
        }
    }

    render() {
      return (
        <div>
            <a href={this.state.fileLocation}>Click here</a> to download your file if it does not happen automatically.
        </div>
      );
    }
  }

  export default withRouter(ViewFile);