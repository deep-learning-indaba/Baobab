import React, { Component } from "react";
import "./EventConfig.css";
import EventConfigComponent from "./components/EventConfigComponent.js";

export default class EventConfig extends Component {
  render() {
    return <EventConfigComponent {...this.props} />;
  }
}
