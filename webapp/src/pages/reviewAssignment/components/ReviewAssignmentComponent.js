import React, { Component } from "react";
import { reviewService } from "../../../services/reviews";
import { withRouter } from "react-router";
import ReactTable from 'react-table'
import 'react-table/react-table.css'
const DEFAULT_EVENT_ID = process.env.DEFAULT_EVENT_ID || 1;

class ReviewAssignmentComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      loading: true,
      reviewers: null,
      error: "",
      newReviewerEmail: ""
      };
  }

  componentDidMount() {
    reviewService.getReviewAssignments(DEFAULT_EVENT_ID).then(result=>{
      console.log(result)
      this.setState({
        loading: false,
        reviewers: result.reviewers,
        error: result.error,
        newReviewerEmail: ""
      });
    });
  }

  handleSubmit = event => {
    event.preventDefault(); // TODO: Figure out what this does
    this.setState({loading: true});

    // If new reviewer is specified, as to list.
    this.state.reviewers.append({
      email: this.state.newReviewerEmail,
      numNewReviews: 0
    })

    // Assign the reviews
    reviewService.assignReviews(DEFAULT_EVENT_ID, this.state.reviewers).then(
      result => {
        // Get updated reviewers, with updated allocations
        return reviewService.getReviewAssignments(DEFAULT_EVENT_ID)
      }, 
      error => this.setState({ error, loading: false})
    ).then(
      result => {
        this.setState({
          loading: false,
          reviewers: result.reviewers,
          error: result.error,
          newReviewerEmail: ""
        });
      },
      error => this.setState({ error, loading: false})
    )
  }

  render() {
    const {loading, reviewers, error, newReviewerEmail} = this.state;

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
      Header: '# Allocated',
      accessor: 'reviews_allocated'
    },{
      Header: '# Completed',
      accessor: 'reviews_completed'
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
      return <div class="alert alert-danger">{error}</div>
    }

    return (
      <div className={"event-stats text-center"}>
      <ReactTable
          data={reviewers}
          columns={columns}
      />        
      </div>
    )
    
  }
}

export default withRouter(ReviewAssignmentComponent);