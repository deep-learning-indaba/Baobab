import React, { Component } from "react";
import "./RegistrationAdmin.css";
import RegistrationAdminComponent from "./components/RegistrationAdminComponent.js"

export default class InvitedGuests extends Component {

  render() {
    return (
      <RegistrationAdminComponent
        {...this.props}>
      </RegistrationAdminComponent>
    );
  }
}