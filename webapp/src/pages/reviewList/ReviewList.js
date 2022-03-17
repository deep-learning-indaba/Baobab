import React, { Component } from "react";
import "./ReviewList.css";
import ReviewListComponent from "./components/ReviewListComponent";

export default class ReviewList extends Component {
  render() {
    return <ReviewListComponent {...this.props} />;
  }
}
