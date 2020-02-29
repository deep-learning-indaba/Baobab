import React, { Component } from "react";
import "./InvitationLetter.css";
import InvitationLetterForm from "./components/InvitationLetterForm.js";

export default class Login extends Component {
  render() {
    return <InvitationLetterForm {
      ...this.props}
    />;
  }
}