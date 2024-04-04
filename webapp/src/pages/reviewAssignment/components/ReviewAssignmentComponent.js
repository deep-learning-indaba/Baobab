import React, { Component } from "react";
import { reviewService } from "../../../services/reviews";
import { withRouter } from "react-router";
import ReactTable from 'react-table'
import { withTranslation } from 'react-i18next'

import 'react-table/react-table.css'

import FormTextBox from "../../../components/form/FormTextBox";
import { tagsService } from '../../../services/tags/tags.service';
import TagSelectorDialog from '../../../components/TagSelectorDialog';

class ReviewAssignmentComponent extends Component {
  constructor(props) {
    super(props);

    this.filterable_tag_types = ["RESPONSE"];

    this.state = {
      loading: true,
      reviewers: null,
      error: "",
      newReviewerEmail: "",
      reviewSummary: {},
      tags: []
    };
  }

  componentDidMount() {
    const event_id = this.props.event ? this.props.event.id : 0;
    const tags = this.state.tags.filter(tag => tag.active).map(tag => tag.id);

    Promise.all([
        tagsService.getTagList(event_id),
        reviewService.getReviewAssignments(event_id),
        reviewService.getReviewSummary(event_id, tags)
    ]).then(responses => {
        this.setState({
            tags: responses[0].tags.filter(tag => this.filterable_tag_types.includes(tag.tag_type)).map(tag => { return { ...tag, active: false } }),
            reviewers: responses[1].reviewers,
            reviewSummary: responses[2].reviewSummary,
            newReviewerEmail: "",
            error: responses[0].error || responses[1].error || responses[2].error,
            loading: false
        }, this.handleData);
    });
  }

  handleChange = event => {
    const value = event.target.value;
    this.setState({ newReviewerEmail: value });
  };

  assignReviewers = (email, toAssign) => {
    // TODO: Clean up! 
    this.setState({ loading: true });

    // Assign the reviews
    const tags = this.state.tags.filter(tag => tag.active).map(tag => tag.id);
    reviewService.assignReviews(this.props.event ? this.props.event.id : 0, email, toAssign, tags).then(
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
        const tags = this.state.tags.filter(tag => tag.active).map(tag => tag.id);
        return reviewService.getReviewSummary(this.props.event ? this.props.event.id : 0, tags);
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

  refreshSummary = () => {
    const tags = this.state.tags.filter(tag => tag.active).map(tag => tag.id);
    reviewService.getReviewSummary(this.props.event ? this.props.event.id : 0, tags).then(
      result => {
        this.setState(prevState => ({
          reviewSummary: result.reviewSummary,
          error: prevState.error + result.error,
        }));
      },
      error => this.setState({ error })
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

  toggleTag = (tag) => {
    const tags = this.state.tags;
    const index = tags.indexOf(tag);
    tags[index].active = !tags[index].active;

    this.setState({ tags }, this.refreshSummary);
  }

  addTag = (reviewer) => {
    const tagIds = reviewer.tags.map(t=>t.id);
    this.setState({
      selectedReviewer: reviewer,
      tagSelectorVisible: true,
      filteredTags: this.state.tags.filter(t=>!tagIds.includes(t.id) && this.filterable_tag_types.includes(t.tag_type))
    })
  }

  onSelectTag = (tag) => {
    reviewService.addReviewerTag({
      reviewerUserId: this.state.selectedReviewer.reviewer_user_id,
      tagId: tag.id,
      eventId: this.props.event.id
    })
    .then(resp => {
      if (resp.status === 201) {
        const newReviewer = {
          ...this.state.selectedReviewer,
          tags: [...this.state.selectedReviewer.tags, tag]
        } 
        const newReviewers = this.state.reviewers.map(r => 
          r.reviewer_user_id === this.state.selectedReviewer.reviewer_user_id  ? newReviewer : r);
        this.setState({
          tagSelectorVisible: false,
          selectedResponse: null,
          filteredTags: [],
          reviewers: newReviewers
        });  // TODO: Call filter reviewers
      }
      else {
        this.setState({
          tagSelectorVisible: false,
          error: resp.error
        });
      }
    });
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
      id: "tags",
      Header: <div className="response-tags">{t("Tags")}</div>,
      Cell: props => <div>
        {props.original.tags.map(t => 
            <span className="tag badge badge-primary" onClick={()=>this.removeTag(props.original, t)} key={`tag_${props.original.response_id}_${t.id}`}>{t.name}</span>)}
        <i className="fa fa-plus-circle" onClick={() => this.addTag(props.original)}></i>
      </div>,
      accessor: u => u.tags.map(t => t.name).join("; "),
      minWidth: 150
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
      <section className="review-assignment-wrapper">
        {error && <div class="alert alert-danger alert-container">
          {error}
        </div>}

        <h2 className="heading">{t('Review Assignment')}</h2>

        <div className="tag-filter">
          <span className="tag-filter-label">{t("Filter by tag")}</span>
          <span className="tags">
            {this.state.tags.map(tag => <span key={"tag_" + tag.id} className={"tag badge " + (tag.active ? "badge-success" : "badge-secondary")} onClick={()=> {this.toggleTag(tag)}}>{tag.name}</span>)}
          </span>
        </div>

        {reviewSummary &&
         <span className="review-unallocated">{t("Total Unallocated Reviews") + ": " + reviewSummary.reviews_unallocated}</span>
        }
       
        <div className="review-assignment-note">{t("review-assignment-filter-note")}</div>

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

        <TagSelectorDialog
            tags={this.state.filteredTags}
            visible={this.state.tagSelectorVisible}
            onCancel={() => this.setState({ tagSelectorVisible: false })}
            onSelectTag={this.onSelectTag}
        />
          
      </section>
    )
  }
}

export default withRouter(withTranslation()(ReviewAssignmentComponent));