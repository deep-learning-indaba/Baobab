import React, { Component } from "react";
import "./Login.css";
import LoginForm from "./components/LoginForm.js"

export default class Login extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <LoginForm loggedIn={this.props.loggedIn}></LoginForm> 
    );
  }
}