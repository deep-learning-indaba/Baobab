import React, { Component } from "react";
import "./EventRoleAdmin.css";
import EventRoleAdminComponent from "./components/EventRoleAdminComponent.js"

export default class EventRoleAdmin extends Component {
  render() {
    return (
      <EventRoleAdminComponent
        {...this.props}>
      </EventRoleAdminComponent>
    );
  }
}