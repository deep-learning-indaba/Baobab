import React, { Component } from "react";
import "./ReviewAssignment.css";
import ReviewAssignmentComponent from "./components/ReviewAssignmentComponent.js"

export default class ReviewAssignment extends Component {
  
  render() {
    return (
      <ReviewAssignmentComponent {...this.props}></ReviewAssignmentComponent> 
    );
  }
}