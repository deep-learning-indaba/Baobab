import React, { Component } from "react";
import { reviewService } from "../../../services/reviews";
import { withRouter } from "react-router";
import ReactTable from 'react-table'
import { withTranslation } from 'react-i18next'

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

  assignReviewers = (email, toAssign) => {
    this.setState({ loading: true });

    // Assign the reviews
    reviewService.assignReviews(this.props.event ? this.props.event.id : 0, email, toAssign).then(
      result => {
        // Get updated reviewers, with updated allocations
        this.setState({
          error: result.error
        })
        return reviewService.getReviewAssignments(this.props.event ? this.props.event.id : 0)
      },
    ).then(
      result => {
        this.setState(prevState => ({
          loading: false,
          reviewers: result.reviewers,
          error: prevState.error + result.error,
          newReviewerEmail: ""
        }));
        return reviewService.getReviewSummary(this.props.event ? this.props.event.id : 0);
      },
      error => this.setState({ error, loading: false })
    )
      .then(
        result => {
          this.setState(prevState => ({
            reviewSummary: result.reviewSummary,
            error: prevState.error + result.error
          }));
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
        }} />
    );
  }

  renderButton = cellInfo => {
    return (
      <button
        className="btn btn-primary btn-sm"
        onClick={() => this.assignReviewers(cellInfo.row.email, cellInfo.row.reviews_to_assign)}
        disabled={!Number.isInteger(cellInfo.row.reviews_to_assign)}>
        {this.props.t("Assign")}
      </button>
    )
  }

  render() {
    const { loading, reviewers, error, newReviewerEmail, reviewSummary } = this.state;

    const loadingStyle = {
      "width": "3rem",
      "height": "3rem"
    }

    const t = this.props.t;

    const columns = [{
      Header: t("Title"),
      accessor: 'user_title' // String-based value accessors!
    }, {
      Header: t("Email"),
      accessor: 'email'
    }, {
      id: 'fullName', // Required because our accessor is not a string
      Header: t("Name"),
      accessor: d => d.firstname + " " + d.lastname // Custom value accessors!
    }, {
      Header: t("No. Allocated"),
      accessor: 'reviews_allocated'
    }, {
      Header: t("No. Completed"),
      accessor: 'reviews_completed'
    }, {
      Header: t("No. to Assign"),
      accessor: 'reviews_to_assign',
      Cell: this.renderEditable
    }, {
      Header: t("Assign"),
      Cell: this.renderButton
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

    return (
      <div className={"review-padding"}>
        {error && <div class="alert alert-danger alert-container">
          {error}
        </div>}

        {reviewSummary &&
         <span className="review-padding">{t("Total Unallocated Reviews:")} {reviewSummary.reviews_unallocated }</span>
        }
       

        <ReactTable
          data={reviewers}
          columns={columns}
          minRows={0} />
        <br />
        <div>
          <FormTextBox
            id={"newReviewEmail"}
            name={'newReviewEmail'}
            label={t("Add new reviewer's email (they must already have an account)")}
            placeholder={t("Review email")}
            onChange={this.handleChange}
            value={newReviewerEmail}
            key={"i_newReviewEmail"} />

          <button
            class="btn btn-primary float-right"
            onClick={() => { this.assignReviewers(this.state.newReviewerEmail, 0) }}>
            {t("Add")}
            </button>

        </div>
      </div>
    )
  }
}

export default withRouter(withTranslation()(ReviewAssignmentComponent));