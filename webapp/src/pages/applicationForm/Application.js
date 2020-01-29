import React, { Component } from "react";
import "./Application.css";
import ApplicationForm from "./components/ApplicationForm"

export default class Application extends Component {
    render() {

      return (
       <ApplicationForm {...this.props}/> 
      );
    }
  }