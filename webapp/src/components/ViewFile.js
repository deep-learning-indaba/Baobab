import React, { Component } from "react";
import { withRouter } from "react-router";
import { withTranslation } from "react-i18next";
import { getDownloadURL } from "../utils/files";

class ViewFile extends Component {
  constructor(props) {
    super(props);
    this.state = {
      fileLocation: null,
    };
  }

  componentDidMount() {
    if (this.props.match && this.props.match.params) {
      const filename = this.props.match.params.filename;
      const fileLocation = getDownloadURL(filename);
      this.setState({
        fileLocation: fileLocation,
      });
      window.location = fileLocation;
    }
  }

  render() {
    const t = this.props.t;
    return (
      <div>
        <a href={this.state.fileLocation}>{t("Click here")}</a>{" "}
        {t("to download your file if it does not happen automatically")}.
      </div>
    );
  }
}

export default withRouter(withTranslation()(ViewFile));
