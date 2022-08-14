import React, { Component } from "react";
import "./Attendance.css";
import IndemnityForm from "./components/IndemnityForm";

export default class Indemnity extends Component {
  render() {
    return (
      <IndemnityForm
        eventId={this.props.event ? this.props.event.id : 0}/>
    );
  }
}
