import React, { Component } from "react";
import "./EventStats.css";
import EventStatsComponent from "./components/EventStatsComponent.js"

export default class EventStats extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <EventStatsComponent></EventStatsComponent> 
    );
  }
}