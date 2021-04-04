import React, { Component } from "react";
import { withRouter } from "react-router";
import ReactTable from "react-table";
import { Link } from "react-router-dom";
import "react-table/react-table.css";

import { reviewService } from "../../../services/reviews";
import { withTranslation } from 'react-i18next'

class ReviewHistoryComponent extends Component {
  constructor(props) {
    super(props);
    this.state = {
      isLoading: true,
      reviewHistory: [],
      isError: false,
      currentPage: 0,
      defaultPageSize: 10,
      selected: null,
      totalPages: null
    };
  }

  componentDidMount() {
    this.loadReviewHistory(this.state.currentPage, this.state.defaultPageSize);
  }

  loadReviewHistory = (pageNumber, pageSize, sortColumn) => {
    reviewService
      .getReviewHistory(this.props.event ? this.props.event.id : 0, pageNumber, pageSize, sortColumn)
      .then(response => {
        this.setState({
          isLoading: false,
          reviewHistory: response.reviewHistory.reviews,
          totalPages: response.reviewHistory.total_pages,
          isError: response.reviews === null,
          errorMessage: response.message,
          currentPage: pageNumber,
        });
      });
  };

  fetchData = (state) => {
    this.setState({ isLoading: true });
    let sortColumn;
    if (state.sorted && state.sorted.length > 0) {
      sortColumn = state.sorted[0].id
    }
    this.loadReviewHistory(state.page, state.pageSize, sortColumn);
  }

  render() {
    const { error,
      isLoading,
      reviewHistory,
      defaultPageSize,
      totalPages
    } = this.state;

    if (error) {
      return <div className={"alert alert-danger alert-container"}>
        {error}
      </div>;
    }

    const t = this.props.t;

    const columns = [
      {
        Header: " ",
        accessor: "response_id",
        Cell: row => {
          return <Link to={"review/" + row.row.response_id}>
            <i className="fa fa-edit"></i></Link>
        },
        filterable: false
      }, 
      {
        Header: "response_id",
        accessor: "response_id",
        filterable: false
      },
      {
        Header: t("Submitted Timestamp"),
        accessor: "submitted_timestamp",
        filterable: false
      }
    ];

    return (
      <div className="ReviewHistory">
        <p className="h5 text-center mb-4">{t("Review History")}</p>

        <div className={"review-padding"}>
          <ReactTable
            loading={isLoading}
            defaultPageSize={defaultPageSize}
            pages={totalPages}
            onFetchData={this.fetchData}
            manual
            data={reviewHistory}
            columns={columns}
            minRows={0} />
        </div>
      </div>
    );
  }
}

export default withRouter(withTranslation()(ReviewHistoryComponent));
