import React, { Component } from "react";
import "./InvitedGuests.css";
import InvitedGuestsComponent from "./components/InvitedGuestComponent.js"

export default class InvitedGuests extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <InvitedGuestsComponent></InvitedGuestsComponent> 
    );
  }
}