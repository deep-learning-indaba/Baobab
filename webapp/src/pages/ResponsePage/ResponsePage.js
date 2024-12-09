import React, { Component } from "react";
import "react-table/react-table.css";
import "./ResponsePage.css";
import { withTranslation } from "react-i18next";
import ReviewModal from "./components/ReviewModal";
import { eventService } from "../../services/events/events.service";
import { applicationFormService } from "../../services/applicationForm/applicationForm.service";
import { reviewService } from "../../services/reviews/review.service";
import { outcomeService } from "../../services/outcome/outcome.service";
import { tagsService } from "../../services/tags/tags.service";
import { responsesService } from "../../services/responses/responses.service";
import AnswerValue from "../../components/answerValue";
import { ConfirmModal } from "react-bootstrap4-modal";
import moment from "moment";
import { getDownloadURL } from "../../utils/files";
import TagSelectorDialog from "../../components/TagSelectorDialog";
import Loading from "../../components/Loading";

class ResponsePage extends Component {
  constructor(props) {
    super(props);

    this.assignable_tag_types = ["RESPONSE"];

    this.state = {
      error: false,
      eventLanguages: [],
      isLoading: true,
      removeTagModalVisible: false,
      removeReviewerModalVisible: false,
      tagToRemove: null,
      reviewToRemove: null,
      tagSelectorVisible: false,
      filteredTagList: [],
      tagList: [],
      assignableTagTypes: ["RESPONSE"],
      reviewResponses: [],
      outcome: { status: null, timestamp: null },
      confirmModalVisible: false,
      pendingOutcome: "",
      confirmationMessage: "",
    };
  }

  componentDidMount() {
    Promise.all([
      eventService.getEvent(this.props.event.id),
      applicationFormService.getForEvent(this.props.event.id),
      responsesService.getResponseDetail(
        this.props.match.params.id,
        this.props.event.id
      ),
      tagsService.getTagList(this.props.event.id),
      reviewService.getReviewAssignments(this.props.event.id),
    ]).then((responses) => {
 
      this.setState(
        {
          eventLanguages: responses[0].event
            ? Object.keys(responses[0].event.name)
            : null,
          event_type: responses[0].event.event_type,
          applicationForm: responses[1].formSpec,
          applicationData: responses[2].detail,
          tagList: responses[3].tags,
          availableReviewers: responses[4].reviewers,
          error:
            responses[0].error ||
            responses[1].error ||
            responses[2].error ||
            responses[3].error ||
            responses[4].error,
        },
        () => {
          this.getOutcome();
          this.getReviewResponses(responses[2].detail);
          this.filterTagList();
        }
      );
    });
  }

  getReviewResponses(applicationData) {
    reviewService
      .getResponseReviewAdmin(applicationData.id, this.props.event.id)
      .then((resp) => {
        if (resp.error) {
          this.setState({
            error: resp.error,
          });
        }
        if (resp.form) {
          this.setState({
            reviewResponses: resp.form.review_responses,
            reviewForm: resp.form.review_form,
            isLoading: false,
            error: resp.error,
          });
        }
      });
  }

  // Misc Functions

  goBack() {
    this.props.history.goBack();
  }

  // Render Page HTML
  // Generate Applciation Status

  formatDate = (dateString) => {
    return moment(dateString).format("D MMM YYYY, H:mm:ss [(UTC)]");
  };

  applicationStatus() {
    const data = this.state.applicationData;
    if (data) {
      const unsubmitted = !data.is_submitted && !data.is_withdrawn;
      const submitted = data.is_submitted;
      const withdrawn = data.is_withdrawn;

      if (unsubmitted) {
        return (
          <span>
            <span class="badge badge-pill badge-secondary">Unsubmitted</span>{" "}
            {this.formatDate(data.started_timestamp)}
          </span>
        );
      }
      if (submitted) {
        return (
          <span>
            <span class="badge badge-pill badge-success">Submitted</span>{" "}
            {this.formatDate(data.submitted_timestamp)}
          </span>
        );
      }
      if (withdrawn) {
        return (
          <span>
            <span class="badge badge-pill badge-danger">Withdrawn</span>{" "}
            {this.formatDate(data.started_timestamp)}
          </span>
        );
      }
    }
  }

  renderReviewResponse(review_response, section) {
    const questions = section.review_questions.map((q) => {
      const a = review_response.scores.find(
        (a) => a.review_question_id === q.id
      );

      if (a) {
        return (
          <div>
            <div key={q.question_id} className="question-answer-block">
              <p>
                <span className="question-headline">{q.headline}</span>
                {q.description && a && (
                  <span className="question-description">
                    <br />
                    {q.description}
                  </span>
                )}
              </p>
              <h6>
                <AnswerValue answer={a} question={q} />
              </h6>
            </div>
          </div>
        );
      }
    });
    return questions;
  }

  // Render Reviews
  renderCompleteReviews() {
    if (this.state.reviewResponses.length) {
      const reviews = this.state.reviewResponses.map((val) => {
        return (
          <div className="section">
            <h4 className="reviewer-section">
              {this.props.t(
                val.reviewer_user_firstname + " " + val.reviewer_user_lastname
              )}
            </h4>
            {this.renderReviewResponse(
              val,
              this.state.reviewForm.review_sections[0]
            )}
          </div>
        );
      });
      return reviews;
    }
  }

  getOutcome() {
    outcomeService
      .getOutcome(this.props.event.id, this.state.applicationData.user_id,this.props.match.params.id)
      .then((response) => {
        console.log(this.props);
        if (response.status === 200) {
          const newOutcome = {
            timestamp: response.outcome.timestamp,
            status: response.outcome.status,
          };
          this.setState({
            outcome: newOutcome,
            isLoading: false,
          });
        } else {
          this.setState({
            error: response.error,
            isLoading: false,
          });
        }
      });
  }

  submitOutcome(selectedOutcome) {
    outcomeService
      .assignOutcome(
        this.state.applicationData.user_id,
        this.props.match.params.id,
        this.props.event.id,
        selectedOutcome
      )
      .then((response) => {
        if (response.status === 201) {
          const newOutcome = {
            timestamp: response.outcome.timestamp,
            status: response.outcome.status,
          };

          this.setState({
            outcome: newOutcome,
            confirmModalVisible: false,
          });
        } else {
          this.setState({ error: response.error });
        }
      });
  }

  openConfirmationModal = (outcome, message) => {
    this.setState({
      confirmModalVisible: true,
      pendingOutcome: outcome,
      confirmationMessage: message,
    });
  };

  handleConfirmation = (outcome, message) => {
    this.setState({
      confirmModalVisible: true,
      pendingOutcome: outcome,
      confirmationMessage: message,
    });
  };

  handleConfirmationOK = (event) => {
    this.setState({
      confirmModalVisible: false,
    });
    this.submitOutcome(this.state.pendingOutcome);
    
  };

  handleConfirmationCancel = (event) => {
    this.setState({
      confirmModalVisible: false,
    });
  };

  renderConfirmationButton(outcome, label, className, message) {
    return (
      <button
        type="button"
        className={`btn ${className}`}
        id={outcome.toLowerCase()}
        onClick={(e) =>
          this.handleConfirmation(outcome, message)
        }
      >
        {label}
      </button>
    );
  }
  
  outcomeStatus() {
    const data = this.state.applicationData;
  
    if (data) {
      if (this.state.outcome.status && this.state.outcome.status !== "REVIEW") {
        const badgeClass =
          this.state.outcome.status === "ACCEPTED"
            ? "badge-success"
            : this.state.outcome.status === "REJECTED"
            ? "badge-danger"
            : "badge-warning";
  
        return (
          <span>
            <span className={`badge badge-pill ${badgeClass}`}>
              {this.state.outcome.status}
            </span>{" "}
            {this.formatDate(this.state.outcome.timestamp)}
          </span>
        );
      }
  
      const { event_type } = this.state;
      const buttons = [];
  
      if (event_type === "JOURNAL" || event_type === "CALL" || event_type === "EVENT") {
        buttons.push(
          this.renderConfirmationButton(
            "ACCEPTED",
            "Accept",
            "btn-success",
            "Are you sure you want to ACCEPT this submission?"
          )
        );
  
        if (event_type === "JOURNAL") {
          buttons.push(
            this.renderConfirmationButton(
              "ACCEPT_W_REVISION",
              "Accept with Minor Revision",
              "btn-warning",
              "Are you sure you want to ACCEPT WITH MINOR REVISION?"
            )
          );
          buttons.push(
            this.renderConfirmationButton(
              "REJECT_W_ENCOURAGEMENT",
              "Reject with Encouragement to Resubmit",
              "btn-warning",
              "Are you sure you want to REJECT WITH ENCOURAGEMENT TO RESUBMIT??"
            )
          );
        }
  
        buttons.push(
          this.renderConfirmationButton(
            "REJECTED",
            "Reject",
            "btn-danger",
            "Are you sure you want to REJECT this submission?"
          )
        );
  
        if (event_type === "EVENT") {
          buttons.push(
            this.renderConfirmationButton(
              "WAITLIST",
              "Waitlist",
              "btn-warning",
              "Are you sure you want to WAITLIST this submission?"
            )
          );
        }
      }
  
      return (
        <div className="user-details">
          {buttons.map((button, index) => (
            <div key={index} className="user-details">
              {button}
            </div>
          ))}
          <ConfirmModal
            visible={this.state.confirmModalVisible}
            onOK={this.handleConfirmationOK}
            onCancel={this.handleConfirmationCancel}
            okText={this.props.t("Yes - Confirm")}
            cancelText={this.props.t("No - Don't confirm")}
          >
            <p>{this.props.t(this.state.confirmationMessage)}</p>
          </ConfirmModal>
        </div>
      );
    }
  }
  

  // Render Sections
  renderSections() {
    const applicationForm = this.state.applicationForm;
    const applicationData = this.state.applicationData;

    let html = [];

    // main function
    if (applicationForm && applicationData) {
      applicationForm.sections.forEach((section) => {
        html.push(
          <div key={section.name} className="section">
            {/*Heading*/}
            <div className="flex baseline">
              <h3>{section.name}</h3>
            </div>
            {/*Q & A*/}
            <div className="Q-A">{this.renderResponses(section)}</div>
          </div>
        );
      });
    }

    return html;
  }

  filterTagList() {
    const tagList = this.state.tagList;
    const responseTagList = tagList.filter((t) =>
      this.state.assignableTagTypes.includes(t.tag_type)
    );
    const applicationData = this.state.applicationData;
    const filteredTagList = responseTagList.filter((tag) => {
      return !applicationData.tags.some((t) => t.id === tag.id);
    });
    this.setState({
      filteredTagList: filteredTagList,
    });
  }

  // Render questions and answers
  renderResponses(section) {
    const applicationData = this.state.applicationData;
    const questions = section.questions.map((q) => {
      const a = applicationData.answers.find((a) => a.question_id === q.id);
      if (q.type === "information") {
        return <h4>{q.headline}</h4>;
      }
      return (
        <div key={q.id} className="question-answer-block">
          <p>
            <span className="question-headline">{q.headline}</span>
            {q.description && (
              <span className="question-description">
                <br />
                {q.description}
              </span>
            )}
          </p>
          <h6>
            <AnswerValue answer={a} question={q} />
          </h6>
        </div>
      );
    });
    return questions;
  }

  // Render Answers
  renderAnswer(id, type, headline, options) {
    const applicationData = this.state.applicationData;
    const baseUrl = process.env.REACT_APP_API_URL;

    const a = applicationData.answers.find((a) => a.question_id === id);
    if (!a) {
      return this.props.t("No answer provided.");
    } else {
      // file
      if (type == "file") {
        return (
          <a
            className="answer file"
            key={a.value}
            target="_blank"
            href={getDownloadURL(a.value)}
          >
            {this.props.t("Uploaded File")}
          </a>
        );
      }
      // multi-file
      else if (type == "multi-file") {
        const answerFiles = JSON.parse(a.value);
        let files = [];
        if (Array.isArray(answerFiles) && answerFiles.length > 0) {
          files = answerFiles.map((file) => (
            <div key={file.name}>
              <a
                key={file.name}
                target="_blank"
                href={getDownloadURL(JSON.stringify(file))}
              >
                {file.name}
              </a>
            </div>
          ));
        } else {
          files = "No files uploaded";
        }
        return <div key={headline}>{files}</div>;
      }
      // choice
      else if (type.includes("choice")) {
        let choices = [];
        options.forEach((opt) => {
          if (a.value == opt.value) {
            choices.push(<div key={opt.label}>{opt.label}</div>);
          }
        });
        return <div key={choices}>{choices}</div>;
      }
      // other
      else {
        return (
          <div key={headline}>
            <p className="answer">{a.value}</p>
          </div>
        );
      }
    }
  }

  // render Delete Modal
  renderDeleteTagModal() {
    const t = this.props.t;

    return (
      <ConfirmModal
        visible={this.state.removeTagModalVisible}
        onOK={this.confirmRemoveTag}
        onCancel={this.cancelRemoveTag}
        okText={t("Yes")}
        cancelText={t("No")}
      >
        <p>{t("Are you sure you want to remove this tag?")}</p>
      </ConfirmModal>
    );
  }

  onSelectTag = (tag) => {
    responsesService
      .tagResponse(this.state.applicationData.id, tag.id, this.props.event.id)
      .then((resp) => {
        if (resp.status === 201) {
          this.setState(
            {
              tagSelectorVisible: false,
              applicationData: {
                ...this.state.applicationData,
                tags: [...this.state.applicationData.tags, tag],
              },
            },
            this.filterTagList
          );
        } else {
          this.setState({
            tagSelectorVisible: false,
            error: resp.error,
          });
        }
      });
  };

  // Del Tag
  removeTag(tag_id) {
    this.setState({
      removeTagModalVisible: true,
      tagToRemove: tag_id,
    });
  }

  confirmRemoveTag = () => {
    const { applicationData, tagToRemove } = this.state;

    responsesService
      .removeTag(applicationData.id, tagToRemove, this.props.event.id)
      .then((resp) => {
        if (resp.status === 200) {
          this.setState(
            {
              removeTagModalVisible: false,
              applicationData: {
                ...this.state.applicationData,
                tags: this.state.applicationData.tags.filter(
                  (t) => t.id !== tagToRemove
                ),
              },
            },
            this.filterTagList
          );
        } else {
          this.setState({
            error: resp.error,
            confirmRemoveTagVisible: false,
          });
        }
      });
  };

  cancelRemoveTag = () => {
    this.setState({
      tagToRemove: null,
      removeTagModalVisible: false,
    });
  };

  renderTags() {
    const data = this.state.applicationData;

    if (data) {
      let tags = data.tags
        ? data.tags.map((tag) => {
            return (
              <span
                className="btn badge badge-primary"
                onClick={() => this.removeTag(tag.id)}
                key={`tag_${tag.id}`}
              >
                {tag.name}
              </span>
            );
          })
        : null;
      return tags;
    }
  }

  // Reviews
  // Render Reviews
  renderReviews() {
    if (this.state.applicationData) {
      if (this.state.applicationData.reviewers) {
        const reviews = this.state.applicationData.reviewers.map(
          (val, index) => {
            let num = index + 1;
            //   {"reviewer_user_id": 4, "user_title": "Mr", "firstname": "Joe", "lastname": "Soap", "status": "completed"},
            return (
              <div className="reviewer">
                <label>{this.props.t("Reviewer") + " " + num}</label>
                <div>
                  <p>
                    {val.user_title} {val.firstname} {val.lastname}
                  </p>

                  {val.status === "completed" && (
                    <p className="review-completed">
                      {this.props.t("Completed")}
                    </p>
                  )}
                  {val.status === "started" && (
                    <p className="review-started">
                      {this.props.t("In Progress")}
                    </p>
                  )}
                  {val.status === "not_started" && (
                    <p className="review-not-started">
                      {this.props.t("Not Started")}
                      <button
                        className="trash-review"
                        onClick={(e) => this.removeReview(val.reviewer_user_id)}
                      >
                        <i className="far fa-trash-alt cursor-pointer"></i>
                      </button>
                    </p>
                  )}
                </div>
              </div>
            );
          }
        );

        return reviews;
      }
    }
  }

  // Remove Reviewer
  removeReview(reviewer_user_id) {
    this.setState({
      removeReviewerModalVisible: true,
      reviewToRemove: reviewer_user_id,
    });
  }

  removeReviewerService() {
    const { applicationData, reviewToRemove } = this.state;
    const { event } = this.props;

    reviewService
      .deleteResponseReviewer(event.id, applicationData.id, reviewToRemove)
      .then((response) => {
        if (response.error) {
          this.setState({
            error: response.error,
            removeTagModalVisible: false,
            removeReviewerModalVisible: false,
            tagToRemove: null,
            reviewToRemove: null,
          });
        } else {
          const newReviewers = applicationData.reviewers.filter(
            (r) => r === null || r.reviewer_user_id !== reviewToRemove
          );

          this.setState({
            applicationData: {
              ...applicationData,
              reviewers: newReviewers,
            },
            removeReviewerModalVisible: false,
          });
        }
      });
  }

  cancelRemoveReviewer() {
    this.setState({
      removeReviewerModalVisible: false,
      reviewToRemove: null,
    });
  }

  postReviewerService(reviewer) {
    const { applicationData } = this.state;

    reviewService
      .assignResponsesToReviewer(
        this.props.event.id,
        [applicationData.id],
        reviewer.email
      )
      .then((response) => {
        if (response.error) {
          this.error(response.error);
        } else {
          const newReviewer = {
            reviewer_user_id: reviewer.reviewer_user_id,
            user_title: reviewer.user_title,
            firstname: reviewer.firstname,
            lastname: reviewer.lastname,
            completed: false,
          };

          const newReviewers = [...applicationData.reviewers, newReviewer];

          this.setState({
            applicationData: {
              ...applicationData,
              reviewers: newReviewers,
            },
          });
        }
      });
  }

  // Render Review Modal
  renderReviewerModal() {
    if (!this.state.reviewResponses || !this.state.applicationData) {
      return <div></div>;
    }
    return (
      <ReviewModal
        handlePost={(data) => this.postReviewerService(data)}
        response={this.state.applicationData}
        reviewers={this.state.availableReviewers.filter(
          (r) =>
            !this.state.applicationData.reviewers.some(
              (rr) => rr.reviewer_user_id === r.reviewer_user_id
            )
        )}
        event={this.props.event}
        t={this.props.t}
      />
    );
  }

  renderDeleteReviewerModal() {
    const t = this.props.t;

    return (
      <ConfirmModal
        visible={this.state.removeReviewerModalVisible}
        onOK={(e) => this.removeReviewerService(e)}
        onCancel={(e) => this.cancelRemoveReviewer(e)}
        okText={t("Yes")}
        cancelText={t("No")}
      >
        <p>{t("Are you sure you want to delete this reviewer?")}</p>
      </ConfirmModal>
    );
  }

  addTag = (response) => {
    const tagIds = response.tags.map((t) => t.id);
    this.setState({
      tagSelectorVisible: true,
      filteredTags: this.state.tags.filter((t) => !tagIds.includes(t.id)),
    });
  };

  setTagSelectorVisible = () => {
    this.setState({
      tagSelectorVisible: true,
    });
  };

  render() {
    const { applicationData, error, isLoading } = this.state;
    // Translation
    const t = this.props.t;

    if (isLoading) {
      return <Loading />;
    }

    return (
      <div className="table-wrapper response-page">
        {/* API Error */}
        {error && (
          <div className="alert alert-danger" role="alert">
            <p>{JSON.stringify(error)}</p>
          </div>
        )}

        {this.renderReviewerModal()}
        {this.renderDeleteTagModal()}
        {this.renderDeleteReviewerModal()}

        {/* Headings */}
        {applicationData && (
          <div className="headings-lower">
            <div className="user-details">
              <h2>
                {applicationData.user_title} {applicationData.firstname}{" "}
                {applicationData.lastname}
              </h2>
              <p>
                {t("Language")}: {applicationData.language}
              </p>
              <div className="tags">
                {this.renderTags()}
                <span
                  className="btn badge badge-add"
                  onClick={() => this.setTagSelectorVisible()}
                >
                  {t("Add tag")}
                </span>
              </div>
            </div>

            {/* User details Right Tab */}
            <div>
              <div className="user-details right">
                <label>{t("Application Status")}</label>{" "}
                <p>{this.applicationStatus()}</p>
                <label>{t("Application Outcome")}</label>{" "}
                <p>{this.outcomeStatus()}</p>
                <button
                  className="btn btn-secondary"
                  onClick={(e) => this.goBack(e)}
                >
                  {t("Go Back")}
                </button>
              </div>
            </div>
          </div>
        )}

        {/*Response Data*/}
        {applicationData && (
          <div className="response-details">
            {/* Reviews */}
            <div className="reviewers-section">
              <h3>{t("Reviewers")}</h3>
              <div className="list">
                {this.renderReviews()}
                <div className="add-reviewer">
                  <button
                    data-toggle="modal"
                    type="button"
                    data-target="#exampleModalReview"
                    className="btn btn-light"
                  >
                    {t("Assign Reviewer")}
                  </button>
                </div>
              </div>
              <div className="divider"></div>
            </div>

            {this.renderSections()}
            {this.state.reviewResponses.length > 0 && (
              <div>
                <div className="divider"></div>
                <div className="reviewers-section">
                  <h3>{t("Reviewer Feedback")}</h3>
                  <h6>
                    {t(
                      "Only feedback for the active review stage is shown below."
                    )}
                  </h6>
                  {this.renderCompleteReviews()}
                </div>
              </div>
            )}
          </div>
        )}

        <TagSelectorDialog
          tags={this.state.filteredTagList}
          visible={this.state.tagSelectorVisible}
          onCancel={() => this.setState({ tagSelectorVisible: false })}
          onSelectTag={this.onSelectTag}
        />
      </div>
    );
  }
}

export default withTranslation()(ResponsePage);
