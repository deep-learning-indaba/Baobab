import React, { Component } from "react";
import "./Registration.css";
import RegistrationComponent from "./components/RegistrationComponent"
import GuestRegistrationComponent from "./components/GuestRegistrationComponent"
import { registrationService } from "../../services/registration";

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

export default class Registration extends Component {

  constructor(props) {
    super(props);
    this.state = {
      GuestRegistration: null
    }
  }

  componentDidMount() {
    registrationService.determineIfGuest(DEFAULT_EVENT_ID).then(response => {
      if (response !== "404") {
        this.setState({
          GuestRegistration: true
        });
      }
      else {
        this.setState({
          GuestRegistration: false
        });
      }
    })
  }
  render() {
    return (
      <div>
        {this.state.GuestRegistration == true ? <GuestRegistrationComponent></GuestRegistrationComponent> : this.state.GuestRegistration == false ? <RegistrationComponent></RegistrationComponent> : ""}
      </div>
    );
  }
}