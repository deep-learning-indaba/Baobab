import React, { Component } from "react";
import "./RegistrationAdmin.css";
import RegistrationAdminComponent from "./components/RegistrationAdminComponent.js"

export default class InvitedGuests extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <RegistrationAdminComponent></RegistrationAdminComponent> 
    );
  }
}