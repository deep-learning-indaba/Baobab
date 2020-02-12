import React, { Component } from "react";
import { reviewService } from "../../../services/reviews";
import { withRouter } from "react-router";
import ReactTable from 'react-table'

import 'react-table/react-table.css'

import FormTextBox from "../../../components/form/FormTextBox";

class ReviewAssignmentComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      loading: true,
      reviewers: null,
      error: "",
      newReviewerEmail: "",
      reviewSummary: {}
    };
  }


  componentDidMount() {
    reviewService.getReviewAssignments(this.props.event ? this.props.event.id : 0).then(result => {
      this.setState({
        loading: false,
        reviewers: result.reviewers,
        error: result.error,
        newReviewerEmail: ""
      });
      return reviewService.getReviewSummary(this.props.event ? this.props.event.id : 0);
    })
      .then(result => {
        this.setState({
          reviewSummary: result.reviewSummary,
          error: result.error
        })
      });

  }

  handleChange = event => {
    const value = event.target.value;
    this.setState({ newReviewerEmail: value });

  };

  handleSubmit = event => {
    event.preventDefault();
    this.setState({ loading: true });

    // If new reviewer is specified, add to list.
    if (this.state.newReviewerEmail !== "") {
      this.state.reviewers.push({
        email: this.state.newReviewerEmail,
        reviews_to_assign: 0
      });
    }

    // Assign the reviews
    reviewService.assignReviews(this.props.event ? this.props.event.id : 0, this.state.reviewers).then(
      result => {
        // Get updated reviewers, with updated allocations
        return reviewService.getReviewAssignments(this.props.event ? this.props.event.id : 0)
      },
      error => this.setState({ error, loading: false })
    ).then(
      result => {
        this.setState({
          loading: false,
          reviewers: result.reviewers,
          error: result.error,
          newReviewerEmail: ""
        });
        return reviewService.getReviewSummary(this.props.event ? this.props.event.id : 0);
      },
      error => this.setState({ error, loading: false })
    )
      .then(
        result => {
          this.setState({
            reviewSummary: result.reviewSummary,
            error: result.error
          });
        },
        error => this.setState({ error, loading: false })
      );
  }

  renderEditable = cellInfo => {
    return (
      <div
        style={{ backgroundColor: "#fafafa" }}
        contentEditable
        suppressContentEditableWarning
        onBlur={e => {
          const reviewers = [...this.state.reviewers];
          const reviewSummary = this.state.reviewSummary;
          reviewers[cellInfo.index][cellInfo.column.id] = parseInt(e.target.innerHTML);
          reviewSummary.reviews_unallocated -= parseInt(e.target.innerHTML);
          this.setState({ reviewSummary });
        }}
        dangerouslySetInnerHTML={{
          __html: this.state.reviewers[cellInfo.index][cellInfo.column.id]
        }}
      />
    );
  }

  render() {
    const { loading, reviewers, error, newReviewerEmail, reviewSummary } = this.state;

    const loadingStyle = {
      "width": "3rem",
      "height": "3rem"
    }

    const columns = [{
      Header: 'Title',
      accessor: 'user_title' // String-based value accessors!
    }, {
      Header: 'Email',
      accessor: 'email'
    }, {
      id: 'fullName', // Required because our accessor is not a string
      Header: 'Name',
      accessor: d => d.firstname + " " + d.lastname // Custom value accessors!
    }, {
      Header: 'No. Allocated',
      accessor: 'reviews_allocated'
    }, {
      Header: 'No. Completed',
      accessor: 'reviews_completed'
    }, {
      Header: 'No. to Assign',
      accessor: 'reviews_to_assign',
      Cell: this.renderEditable
    }]

    if (loading) {
      return (
        <div class="d-flex justify-content-center">
          <div class="spinner-border" style={loadingStyle} role="status">
            <span class="sr-only">Loading...</span>
          </div>
        </div>
      )
    }

    if (error) {
      return <div class="alert alert-danger alert-container">
        {error}
      </div>
    }

    return (
      <form onSubmit={this.handleSubmit}>
        <div className={"review-padding"}>
          <span className="review-padding">Total Unallocated Reviews: {reviewSummary.reviews_unallocated}</span>
          <ReactTable
            data={reviewers}
            columns={columns}
            minRows={0}
          />
          <div>
            <FormTextBox
              Id={"newReviewEmail"}
              name={'newReviewEmail'}
              label={"Add new reviewer's email"}
              placeholder={"Review email"}
              onChange={this.handleChange}
              value={newReviewerEmail}
              key={"i_newReviewEmail"}
            />
            <button
              class="btn btn-primary float-right"
              type="submit">
              Assign
            </button>
          </div>
        </div>
      </form>
    )
  }
}

export default withRouter(ReviewAssignmentComponent);