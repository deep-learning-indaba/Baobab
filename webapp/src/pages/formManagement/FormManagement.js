import React, { Component } from "react";
import "./FormManagement.css";
import FormManagementComponent from "./components/FormManagementComponent.js"

export default class FormManagement extends Component {

  render() {
    return (
      <FormManagementComponent
        {...this.props}>
      </FormManagementComponent>
    );
  }
}
