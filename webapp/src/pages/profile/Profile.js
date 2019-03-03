import React, { Component } from "react";
import { userService } from '../../services/user';
import "./Profile.css";
import ProfileForm from "./components/ProfileForm";

export default class Profile extends Component {
  constructor(props) {
    super(props);
  }
  render() {
    return (
      <ProfileForm loggedIn={this.props.loggedIn}></ProfileForm>
    );
  }
}