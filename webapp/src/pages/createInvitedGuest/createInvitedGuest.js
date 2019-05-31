import React, { Component } from "react";
import CreateInvitedGuestsComponent from "./components/createInvitedGuestComponent.js";
import queryString from "query-string";

export default class CreateInvitedGuests extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    let url = this.props.location.search;
    let params = queryString.parse(url);
    console.log(params);
    return (
      <CreateInvitedGuestsComponent email={params.email} role={params.role} />
    );
  }
}
