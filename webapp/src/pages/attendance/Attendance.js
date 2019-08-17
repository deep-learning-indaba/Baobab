import React, { Component } from "react";
import "./Attendance.css";
import AttendanceTable from "./components/AttendanceTable";
const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;
export default class Attendance extends Component {
  render() {
    return <AttendanceTable eventId={DEFAULT_EVENT_ID} />;
  }
}
