import React, { Component } from "react";
import "./Registration.css";
import RegistrationComponent from "./components/RegistrationComponent"
import GuestRegistrationComponent from "./components/GuestRegistrationComponent"
import { invitedGuestServices } from '../../services/invitedGuests/invitedGuests.service';

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

export default class Registration extends Component {

  constructor(props) {
    super(props);
    this.state = {
      GuestRegistration: null
    }
  }

  componentDidMount() {
    invitedGuestServices.determineIfInvitedGuest(DEFAULT_EVENT_ID).then(response => {
      if (response.statusCode === "200") {
        this.setState({
          GuestRegistration: true
        });
      }
      else if (response.statusCode ==="404"){
        this.setState({
          GuestRegistration: false
        });
      }
    })
  }
  render() {
    return (
      <div>
        {this.state.GuestRegistration === true ? <GuestRegistrationComponent></GuestRegistrationComponent> : this.state.GuestRegistration === false ? <RegistrationComponent></RegistrationComponent> : ""}
      </div>
    );
  }
}