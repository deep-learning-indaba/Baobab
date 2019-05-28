import React, { Component } from "react";
import CreateInvitedGuestsComponent from "./components/createInvitedGuestComponent.js"

export default class CreateInvitedGuests extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <CreateInvitedGuestsComponent></CreateInvitedGuestsComponent> 
    );
  }
}