import React, { Component } from "react";
import EventStatsComponent from "./components/EventStatsComponent.js"

export default class EventStats extends Component {
  render() {
    return (
      <EventStatsComponent
        {...this.props}>
      </EventStatsComponent>
    );
  }
}