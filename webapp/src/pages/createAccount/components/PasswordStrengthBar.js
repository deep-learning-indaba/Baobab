import React, { Component } from "react";
import PasswordStrengthBar from "react-password-strength-bar";

class PasswordStrengthBar extends Component {
  render() {
    return <PasswordStrengthBar password={this.props.password} />;
  }
}

export default PasswordStrengthBar;
