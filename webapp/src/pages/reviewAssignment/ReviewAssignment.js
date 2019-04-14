import React, { Component } from "react";
import "./ReviewAssignment.css";
import ReviewAssignmentComponent from "./components/ReviewAssignmentComponent.js"

export default class ReviewAssignment extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <ReviewAssignmentComponent></ReviewAssignmentComponent> 
    );
  }
}