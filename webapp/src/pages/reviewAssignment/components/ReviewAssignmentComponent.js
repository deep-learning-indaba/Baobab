import React, { Component } from "react";
import { reviewService } from "../../../services/reviews";
import { withRouter } from "react-router";
import ReactTable from 'react-table'
import { withTranslation } from 'react-i18next'

import 'react-table/react-table.css'

import FormTextBox from "../../../components/form/FormTextBox";
import { tagsService } from '../../../services/tags/tags.service';
import TagSelectorDialog from '../../../components/TagSelectorDialog';
import { ConfirmModal } from "../../../components/Modal";

class ReviewAssignmentComponent extends Component {
  constructor(props) {
    super(props);

    this.filterable_tag_types = ["RESPONSE"];

    this.state = {
      loading: true,
      reviewers: null,
      filteredReviewers: null,
      error: "",
      newReviewerEmail: "",
      reviewSummary: {},
      tags: [],
      filteredTags: []
    };
  }

  isNewStyleEvent() {
    return this.props.event && this.props.event.review_form_id;
  }

  componentDidMount() {
    const event_id = this.props.event ? this.props.event.id : 0;

    if (this.isNewStyleEvent()) {
      const reviewFormId = this.props.event.review_form_id;
      Promise.all([
        tagsService.getTagList(event_id),
        reviewService.getFormReviewAssignments(reviewFormId, event_id),
        reviewService.getFormReviewSummary(reviewFormId, event_id, [])
      ]).then(responses => {
        const tagList = (responses[0].tags || []).filter(
          tag => this.filterable_tag_types.includes(tag.tag_type)
        ).map(tag => ({ ...tag, active: false }));
        this.setState({
          tags: tagList,
          reviewers: responses[1].reviewers || [],
          filteredReviewers: responses[1].reviewers || [],
          reviewSummary: responses[2].reviewSummary,
          newReviewerEmail: '',
          error: responses[0].error || responses[1].error || responses[2].error,
          loading: false
        });
      });
      return;
    }

    const tags = this.state.tags.filter(tag => tag.active).map(tag => tag.id);

    Promise.all([
        tagsService.getTagList(event_id),
        reviewService.getReviewAssignments(event_id),
        reviewService.getReviewSummary(event_id, tags)
    ]).then(responses => {
        this.setState({
            tags: responses[0].tags.filter(tag => this.filterable_tag_types.includes(tag.tag_type)).map(tag => { return { ...tag, active: false } }),
            reviewers: responses[1].reviewers,
            filteredReviewers: responses[1].reviewers,
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
    this.setState({ loading: true });
    const event_id = this.props.event ? this.props.event.id : 0;

    if (this.isNewStyleEvent()) {
      const reviewFormId = this.props.event.review_form_id;
      const activeTags = this.state.tags.filter(tag => tag.active).map(tag => tag.id);
      reviewService.assignFormReviews(
        reviewFormId, event_id, email, toAssign, activeTags
      ).then(result => {
        return Promise.all([
          reviewService.getFormReviewAssignments(reviewFormId, event_id),
          reviewService.getFormReviewSummary(reviewFormId, event_id, activeTags)
        ]).then(responses => {
          this.setState({
            loading: false,
            reviewers: responses[0].reviewers || [],
            filteredReviewers: responses[0].reviewers || [],
            reviewSummary: responses[1].reviewSummary,
            newReviewerEmail: '',
            error: result.error || responses[0].error || responses[1].error
          });
        });
      });
      return;
    }

    // Legacy path
    const tags = this.state.tags.filter(tag => tag.active).map(tag => tag.id);
    reviewService.assignReviews(event_id, email, toAssign, tags).then(
      result => {
        this.setState({
          error: result.error
        })
        return reviewService.getReviewAssignments(event_id)
      },
    ).then(
      result => {
        this.setState(prevState => ({
          loading: false,
          reviewers: result.reviewers,
          filteredReviewers: this.filterReviewers(result.reviewers, this.state.tags),
          error: prevState.error + result.error,
          newReviewerEmail: ""
        }));
        const tags = this.state.tags.filter(tag => tag.active).map(tag => tag.id);
        return reviewService.getReviewSummary(event_id, tags);
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

  removeReviewers = (email, toRemove) => {
    this.setState({ loading: true });
    const event_id = this.props.event ? this.props.event.id : 0;

    if (this.isNewStyleEvent()) {
      const reviewFormId = this.props.event.review_form_id;
      const activeTags = this.state.tags.filter(tag => tag.active).map(tag => tag.id);
      reviewService.removeFormReviews(
        reviewFormId, event_id, email, toRemove, activeTags
      ).then(result => {
        return Promise.all([
          reviewService.getFormReviewAssignments(reviewFormId, event_id),
          reviewService.getFormReviewSummary(reviewFormId, event_id, activeTags)
        ]).then(responses => {
          this.setState({
            loading: false,
            reviewers: responses[0].reviewers || [],
            filteredReviewers: responses[0].reviewers || [],
            reviewSummary: responses[1].reviewSummary,
            error: result.error || responses[0].error || responses[1].error
          });
        });
      });
      return;
    }

    // Legacy path
    const tags = this.state.tags.filter(tag => tag.active).map(tag => tag.id);
    reviewService.removeReviews(event_id, email, toRemove, tags).then(
      result => {
        this.setState({
          error: result.error
        })
        return reviewService.getReviewAssignments(event_id)
      },
    ).then(
      result => {
        this.setState(prevState => ({
          loading: false,
          reviewers: result.reviewers,
          filteredReviewers: this.filterReviewers(result.reviewers, this.state.tags),
          error: prevState.error + result.error
        }));
        const tags = this.state.tags.filter(tag => tag.active).map(tag => tag.id);
        return reviewService.getReviewSummary(event_id, tags);
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
        className="bg-slate-50 border border-border rounded px-2 py-1 text-center outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all text-sm font-medium"
        contentEditable
        suppressContentEditableWarning

        onBlur={e => {
          const reviewers = [...this.state.filteredReviewers];
          const reviewSummary = this.state.reviewSummary;
          reviewers[cellInfo.index][cellInfo.column.id] = parseInt(e.target.innerHTML);
          this.setState({ reviewSummary });
        }}

        dangerouslySetInnerHTML={{
          __html: this.state.reviewers[cellInfo.index][cellInfo.column.id]
        }} />
    );
  }

  refreshSummary = () => {
    const event_id = this.props.event ? this.props.event.id : 0;
    const tags = this.state.tags.filter(tag => tag.active).map(tag => tag.id);
    if (this.isNewStyleEvent()) {
      reviewService.getFormReviewSummary(this.props.event.review_form_id, event_id, tags).then(
        result => {
          this.setState({
            reviewSummary: result.reviewSummary,
            error: result.error
          });
        },
        error => this.setState({ error })
      );
      return;
    }
    reviewService.getReviewSummary(event_id, tags).then(
      result => {
        this.setState(prevState => ({
          reviewSummary: result.reviewSummary,
          error: prevState.error + result.error,
        }));
      },
      error => this.setState({ error })
    );
  }

  renderAssignButton = cellInfo => {
    return (
      <button
        className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50 cursor-pointer"
        onClick={() => this.assignReviewers(cellInfo.row.email, cellInfo.row.reviews_to_assign)}
        disabled={!Number.isInteger(cellInfo.row.reviews_to_assign)}>
        {this.props.t("Assign")}
      </button>
    )
  }

  renderRemoveButton = cellInfo => {
    return (
      <button
        className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors bg-error text-error-foreground hover:bg-error/90 shadow-sm disabled:opacity-50 cursor-pointer"
        onClick={() => this.removeReviewers(cellInfo.row.email, cellInfo.row.reviews_to_remove)}
        disabled={!Number.isInteger(cellInfo.row.reviews_to_remove)}>
        {this.props.t("Remove")}
      </button>
    )
  }

  toggleTag = (tag) => {
    const tags = this.state.tags;
    const index = tags.indexOf(tag);
    tags[index].active = !tags[index].active;

    this.setState(prevState => ({ 
      tags,
      filteredReviewers: this.filterReviewers(prevState.reviewers, tags)
    }), this.refreshSummary);
  }

  filterReviewers = (reviewers, tags) => {
    return reviewers;
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
        this.setState(prevState => ({
          tagSelectorVisible: false,
          selectedResponse: null,
          filteredTags: [],
          reviewers: newReviewers,
          filteredReviewers: this.filterReviewers(newReviewers, prevState.tags)
        }));
      }
      else {
        this.setState({
          tagSelectorVisible: false,
          error: resp.error
        });
      }
    });
  }

  removeTag = (reviewer, tag) => {
    this.setState({
      selectedReviewer: reviewer,
      selectedTag: tag,
      confirmRemoveTagVisible: true
    });
  }

  confirmRemoveTag = () => {
    const {selectedReviewer, selectedTag} = this.state;

    reviewService.deleteReviewerTag(selectedReviewer.reviewer_user_id, selectedTag.id, this.props.event.id)
    .then(resp => {
      if (resp.error === "") {
        const newReviewer = {
          ...selectedReviewer,
          tags: selectedReviewer.tags.filter(t=>t.id !== selectedTag.id)
        }
        const newReviewers = this.state.reviewers.map(r => 
            r.reviewer_user_id === selectedReviewer.reviewer_user_id ? newReviewer : r);
        this.setState({
          reviewers: newReviewers,
          confirmRemoveTagVisible: false,
          filteredReviewers: this.filterReviewers(newReviewers, this.state.tags)
        });
      }
      else {
        this.setState({
          error: resp.error,
          confirmRemoveTagVisible: false
        });
      }
    })
  }

  render() {
    const { loading, filteredReviewers, error, newReviewerEmail, reviewSummary } = this.state;

    const t = this.props.t;

    if (loading) {
      return (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      );
    }

    const columns = [{
      Header: <div className="text-left font-bold">{t("Title")}</div>,
      accessor: 'user_title'
    }, {
      Header: <div className="text-left font-bold">{t("Email")}</div>,
      accessor: 'email'
    }, {
      id: 'fullName',
      Header: <div className="text-left font-bold">{t("Name")}</div>,
      accessor: d => d.firstname + " " + d.lastname
    }, {
      id: "tags",
      Header: <div className="response-tags text-left font-bold">{t("Tags")}</div>,
      Cell: props => <div className="tags flex flex-wrap gap-1 items-center">
        {props.original.tags.map(t => 
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20 cursor-pointer select-none" onClick={()=>this.removeTag(props.original, t)} key={`tag_${props.original.response_id}_${t.id}`}>{t.name}</span>)}
        <i className="fa fa-plus-circle text-primary hover:text-primary/80 transition-colors text-base cursor-pointer" onClick={() => this.addTag(props.original)}></i>
      </div>,
      accessor: u => u.tags.map(t => t.name).join("; "),
      minWidth: 150
    }, {
      Header: <div className="text-left font-bold">{t("No. Allocated")}</div>,
      accessor: 'reviews_allocated'
    }, {
      Header: <div className="text-left font-bold">{t("No. Completed")}</div>,
      accessor: 'reviews_completed'
    }, {
      id: "percent_complete",
      Header: <div className="text-left font-bold">{t("% Completed")}</div>,
      accessor: u => u.reviews_allocated === 0 ? 100 : (u.reviews_completed / u.reviews_allocated) * 100,
      Cell: props => <div> {props.value.toLocaleString(undefined, { minimumFractionDigits: 1 })} </div>
    }, {
      Header: <div className="text-left font-bold">{t("No. to Assign")}</div>,
      accessor: 'reviews_to_assign',
      Cell: this.renderEditable
    }, {
      Header: <div className="text-left font-bold">{t("Assign")}</div>,
      Cell: this.renderAssignButton
    }, {
      Header: <div className="text-left font-bold">{t("No. to Remove")}</div>,
      accessor: 'reviews_to_remove',
      Cell: this.renderEditable
    }, {
      Header: <div className="text-left font-bold">{t("Remove")}</div>,
      Cell: this.renderRemoveButton
    }
  ];

    return (
      <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-6">
        <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6">
          {error && (
            <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
              {error}
            </div>
          )}

          <div>
            <h1 className="font-heading text-2xl font-bold text-foreground mb-1">{t('Review Assignment')}</h1>
            <p className="text-sm text-muted-foreground">{t('Review allocations and assign candidates to reviewers.')}</p>
          </div>

          <div className="space-y-2">
            <span className="block text-sm font-semibold text-foreground/90">{t("Filter by tag")}</span>
            <div className="flex flex-wrap gap-2">
              {this.state.tags.map(tag => (
                <span 
                  key={"tag_" + tag.id} 
                  className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold cursor-pointer border transition-colors select-none ${tag.active ? "bg-green-50 text-green-700 border-green-200" : "bg-slate-50 text-muted-foreground border-border hover:bg-slate-100"}`} 
                  onClick={()=> {this.toggleTag(tag)}}
                >
                  {tag.name}
                </span>
              ))}
            </div>
          </div>

          {reviewSummary && (
            <div className="bg-primary/5 border border-primary/10 rounded-xl p-4 text-sm font-semibold text-primary">
              {t("Total Unallocated Reviews") + ": " + reviewSummary.reviews_unallocated}
            </div>
          )}
        
          <div className="text-xs text-muted-foreground leading-relaxed italic bg-slate-50 border border-border/50 p-4 rounded-xl">
            {t("review-assignment-filter-note")}
          </div>

          <div className="react-table">
            <ReactTable
              data={filteredReviewers}
              columns={columns}
              minRows={0}
              className="ReactTable"
            />
          </div>

          <div className="pt-6 border-t border-border/50 space-y-4">
            <h3 className="text-base font-bold text-foreground/90">{t("Add New Reviewer")}</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
              <div className="md:col-span-3">
                <FormTextBox
                  id={"newReviewEmail"}
                  name={'newReviewEmail'}
                  label={t("Add new reviewer's email (they must already have an account)")}
                  placeholder={t("Review email")}
                  onChange={this.handleChange}
                  value={newReviewerEmail}
                  key={"i_newReviewEmail"}
                />
              </div>
              <div>
                <button
                  type="button"
                  className="w-full inline-flex items-center justify-center px-5 py-3 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm cursor-pointer"
                  onClick={() => { this.assignReviewers(this.state.newReviewerEmail, 0) }}>
                  {t("Add")}
                </button>
              </div>
            </div>
          </div>
        </div>

        <TagSelectorDialog
            tags={this.state.filteredTags}
            visible={this.state.tagSelectorVisible}
            onCancel={() => this.setState({ tagSelectorVisible: false })}
            onSelectTag={this.onSelectTag}
        />

        <ConfirmModal
            visible={this.state.confirmRemoveTagVisible}
            onOK={this.confirmRemoveTag}
            onCancel={() => this.setState({ confirmRemoveTagVisible: false })}
            okText={t("Yes")}
            cancelText={t("No")}>
            <p>
                {t('Are you sure you want to remove this tag?')}
            </p>
        </ConfirmModal>
          
      </div>
    )
  }
}

export default withRouter(withTranslation()(ReviewAssignmentComponent));