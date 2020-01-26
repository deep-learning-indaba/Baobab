import React, { Component } from "react";
import "./Registration.css";
import RegistrationComponent from "./components/RegistrationComponent"
import GuestRegistrationComponent from "./components/GuestRegistrationComponent"
import { invitedGuestServices } from '../../services/invitedGuests/invitedGuests.service';

export default class Registration extends Component {

  constructor(props) {
    super(props);
    this.state = {
      GuestRegistration: null
    }
  }

  componentDidMount() {
    invitedGuestServices.determineIfInvitedGuest(this.props.event.id).then(response => {
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
        {this.state.GuestRegistration === true ? <GuestRegistrationComponent {...this.props}></GuestRegistrationComponent> : this.state.GuestRegistration === false ? <RegistrationComponent {...this.props}></RegistrationComponent> : ""}
      </div>
    );
  }
}