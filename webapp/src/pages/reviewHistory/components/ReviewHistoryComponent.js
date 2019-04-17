import React, { Component } from "react";
import { withRouter } from "react-router";
import ReactTable from "react-table";

import "react-table/react-table.css";

import { reviewService } from "../../../services/reviews";
import { createColClassName } from "../../../utils/styling/styling";
import { columns } from "./tablecolumns";

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

class ReviewHistoryComponent extends Component {
  constructor(props) {
    super(props);
    this.state = {
      isLoading: true,
      reviewHistory: null,
      isError: false
    };
  }

  componentDidMount() {
    this.loadReviewHistory();
  }

  loadReviewHistory = () => {
    let pageNumber = 0;
    let limit = 20;
    reviewService
      .getReviewHistory(DEFAULT_EVENT_ID, pageNumber, limit)
      .then(response => {
        this.setState({
          isLoading: false,
          reviewHistory: response.reviews,
          isError: response.reviews === null,
          errorMessage: response.message
        });
      });
  };

  submit = () => {};

  render() {
    const { error, isLoading, reviewHistory } = this.state;

    const loadingStyle = {
      width: "3rem",
      height: "3rem"
    };

    if (isLoading) {
      return (
        <div class="d-flex justify-content-center">
          <div class="spinner-border" style={loadingStyle} role="status">
            <span class="sr-only">Loading...</span>
          </div>
        </div>
      );
    }

    if (error) {
      return <div className={"alert alert-danger"}>{error}</div>;
    }

    return (
      <div className="ReviewHistory">
        <p className="h5 text-center mb-4">Review History</p>
        <div className={"review-padding"}>
          <ReactTable data={reviewHistory} columns={columns} minRows={0} />;
        </div>
      </div>
    );
  }
}

export default withRouter(ReviewHistoryComponent);
