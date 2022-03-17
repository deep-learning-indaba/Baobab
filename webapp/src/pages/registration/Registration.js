import React, { Component } from "react";
import "./Registration.css";
import RegistrationComponent from "./components/RegistrationComponent";
import GuestRegistrationComponent from "./components/GuestRegistrationComponent";
import { invitedGuestServices } from "../../services/invitedGuests/invitedGuests.service";

export default class Registration extends Component {
  constructor(props) {
    super(props);
    this.state = {
      GuestRegistration: null,
    };
  }

  componentDidMount() {
    invitedGuestServices
      .determineIfInvitedGuest(this.props.event ? this.props.event.id : 0)
      .then((response) => {
        if (response.statusCode === "200") {
          this.setState({
            GuestRegistration: true,
          });
        } else if (response.statusCode === "404") {
          this.setState({
            GuestRegistration: false,
          });
        }
      });
  }
  render() {
    if (this.props.event && !this.props.event.registration_open) {
      return <div class="alert alert-danger">Registration is now closed</div>;
    }
    return (
      <div>
        {this.state.GuestRegistration === true ? (
          <GuestRegistrationComponent
            {...this.props}
          ></GuestRegistrationComponent>
        ) : this.state.GuestRegistration === false ? (
          <RegistrationComponent {...this.props}></RegistrationComponent>
        ) : (
          ""
        )}
      </div>
    );
  }
}
