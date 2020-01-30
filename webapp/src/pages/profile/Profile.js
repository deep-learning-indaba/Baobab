import React, { Component } from "react";
import "./Profile.css";
import ProfileForm from "./components/ProfileForm";

export default class Profile extends Component {

  render() {
    return (
      <ProfileForm loggedIn={this.props.loggedIn} {...this.props}></ProfileForm>
    );
  }
}