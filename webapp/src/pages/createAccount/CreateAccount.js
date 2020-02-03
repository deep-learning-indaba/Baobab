import React, { Component } from "react";
import "./CreateAccount.css";
import CreateAccountForm from "./components/CreateAccountForm";

export default class CreateAccount extends Component {
  render() {
    return (
      <CreateAccountForm loggedIn={this.props.loggedIn} organisation={this.props.organisation}></CreateAccountForm> 
    );
  }
}