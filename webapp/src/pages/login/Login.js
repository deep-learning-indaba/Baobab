import React, { Component } from "react";
import "./Login.css";
import LoginForm from "./components/LoginForm.js"

export default class Login extends Component {

  render() {
    return (
      <LoginForm
        loggedIn={this.props.loggedIn}
        organisation={this.props.organisation}>
      </LoginForm>
    );
  }
}