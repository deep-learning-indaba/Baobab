import React, { Component } from "react";
import { Redirect } from "react-router-dom";
import "./Application.css";
import ApplicationForm from "./components/ApplicationForm"

export default class Application extends Component {
  render() {
    if (this.props.event && this.props.event.application_form_id) {
      return <Redirect to={"/" + this.props.event.key + "/forms/" + this.props.event.application_form_id} />;
    }

    return (
      <ApplicationForm
        {...this.props} />
    );
  }
}