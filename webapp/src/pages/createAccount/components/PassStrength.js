import React, { Component } from "react";
import PasswordStrengthBar from "react-password-strength-bar";

class PassStrength extends Component {
  render() {
    return <PasswordStrengthBar password={this.props.password} />;
  }
}

export default PassStrength;
