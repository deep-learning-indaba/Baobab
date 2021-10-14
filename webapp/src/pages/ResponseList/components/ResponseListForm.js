import React, { Component } from "react";
import "../ResponseList.css";
import { Trans, withTranslation } from "react-i18next";
import { responsesService } from "../../../services/responses/responses.service";
import ReactTable from "react-table";
import "react-table/react-table.css";
import ReactTooltip from "react-tooltip";
import { NavLink } from "react-router-dom";
import { tagsService } from "../../../services/tags/tags.service";
import { applicationFormService } from "../../../services/applicationForm/applicationForm.service";
import AnswerValue from "../../../components/answerValue";
import Loading from "../../../components/Loading";
import FormTextBox from "../../../components/form/FormTextBox";
import { reviewService } from "../../../services/reviews/review.service";

class ResponseListForm extends Component {
  constructor(props) {
    super(props);
    this.state = {
      questions: [],
      selectedQuestions: [],
      toggleList: false,
      responseTable: null,
      btnUpdate: false,
      selectedTags: [],
      includeUnsubmitted: false,
      responses: null,
      tags: null,
      error: null,
      isLoading: true,
    };
  }

  componentWillMount() {
    Promise.all([
      tagsService.getTagList(this.props.event.id),
      responsesService.getResponseList(this.props.event.id, false, []),
      applicationFormService.getQuestionList(this.props.event.id),
    ]).then((responses) => {
      console.log(responses);
      this.setState(
        {
          tags: responses[0].tags,
          responses: responses[1].responses,
          questions: responses[2].questions
            ? responses[2].questions.filter((q) => q.type !== "information")
            : null,
          error: responses[0].error || responses[1].error || responses[2].error,
          isLoading: false,
        },
        this.handleData
      );
    });
  }

  refreshResponses() {
    this.toggleList(false);
    const { selectedTags, selectedQuestions, includeUnsubmitted } = this.state;

    responsesService
      .getResponseList(
        this.props.event.id,
        includeUnsubmitted,
        selectedQuestions
      )
      .then((resp) => {
        this.setState(
          {
            responses: resp.responses.filter(
              (r) =>
                selectedTags.length == 0 ||
                r.tags.map((t) => t.name).some((t) => selectedTags.includes(t))
            ),
            error: resp.error,
          },
          this.handleData
        );
      });
  }

  // Handle/Format Data
  handleData = () => {
    const { questions, responses } = this.state;

    if (!responses) {
      console.log("ERROR: responses is not defined: ", responses);
      return;
    }

    this.setState({
      selectedResponseIds: responses.map((r) => r.response_id),
    });

    // disable question list
    this.toggleList(false);

    // Handle Answers and Reviews

    // TODO: Change this to a map and don't mutate the state.
    responses.forEach((val) => {
      let handleAnswers = [];
      let handleReviews = [];
      let handleTags = [];

      // Create Response Id Link
      if (this.props.event) {
        val.response_id = (
          <NavLink
            to={`/${this.props.event.key}/responsePage/${val.response_id}`}
            className="table-nav-link"
          >
            {val.response_id}
          </NavLink>
        );
      }

      val.answers.forEach((answer) => {
        const question = questions.find(
          (q) => answer.question_id === q.question_id
        );
        handleAnswers.push([
          {
            headline: answer.headline,
            value: (
              <div key={answer.headline} data-tip={answer.value}>
                <AnswerValue answer={answer} question={question} />
                <ReactTooltip className="Tooltip" />
              </div>
            ),
          },
        ]);
      });

      // extract only the tag names
      val.tags.forEach((tag) => {
        if (tag) {
          handleTags.push(<div>{tag.name}</div>);
        }
      });

      // extract only the reviewers name
      val.reviewers.forEach((review) => {
        review
          ? handleReviews.push(review.reviewer_name)
          : handleReviews.push("");
      });

      // add User Title as new column
      function userTitleCol(row, user_title, firstname, lastname) {
        return (row.user = user_title + " " + firstname + " " + lastname);
      }

      // envoke and store new columns for UserTitle
      // combine user credentials
      userTitleCol(val, val.user_title, val.firstname, val.lastname);

      // insert Answers values as columns
      if (handleAnswers.length) {
        handleAnswers.forEach((answer, index) => {
          let key = answer[0].headline;
          val[key] = answer[0].value;
        });
        handleAnswers = [];
      }
      // insert new reviews values as columns
      if (handleReviews.length) {
        handleReviews.forEach((review, index) => {
          let num = index + 1;
          let key = this.props.t("Reviewer") + " " + num;
          val[key] = review;
          handleReviews = [];
        });
      }

      val.tags = handleTags;
      val.is_submitted = val.is_submitted ? "True" : "False";
      val.is_withdrawn = val.is_withdrawn ? "True" : "False";

      // delete original review and answer rows as they don't need to be displayed with all their data
      delete val.answers;
      delete val.reviewers;
      delete val.user_title;
      delete val.firstname;
      delete val.lastname;
    });

    this.setState({
      responseTable: responses,
      btnUpdate: false,
    });
  };

  // Tag Selection State
  tagSelector(name) {
    const list = this.state.selectedTags;
    const duplicateTag = list.indexOf(name); // test against duplicates

    duplicateTag == -1 ? list.push(name) : list.splice(duplicateTag, 1);

    this.setState({
      selectedTags: list,
      btnUpdate: true,
    });
  }

  // Delete Pill function
  deletePill(val) {
    this.tagSelector(val);
    this.refreshResponses();
  }

  // Question selection state
  questionSelector(question) {
    const selected = this.state.selectedQuestions;
    let duplicate = selected.indexOf(question);

    duplicate == -1 ? selected.push(question) : selected.splice(duplicate, 1);
    this.setState({
      selectedQuestions: selected,
      btnUpdate: true,
    });
  }

  // Toggle List
  toggleList(list, type) {
    this.setState({
      toggleList: !list ? type : false,
    });
  }

  // Generate table columns
  generateCols() {
    let colFormat = [];
    // Find the row with greatest col count and assign the col values to React Table
    if (this.state.responseTable) {
      // function
      function readColumns(rows) {
        let tableColumns = [
          "response_id",
          "user",
          "start_date",
          "is_submitted",
          "is_withdrawn",
          "submitted_date",
          "tags",
        ];
        rows.map((val) => {
          let newColumns = Object.keys(val);
          newColumns.forEach((val) => {
            if (!tableColumns.includes(val)) {
              tableColumns.push(val);
            }
          });
        });
        return tableColumns;
      }

      // function
      function widthCalc(colItem) {
        if (colItem.includes("question")) {
          return 200;
        }

        if (
          colItem.includes("user") ||
          colItem.includes("Review") ||
          colItem.includes("date")
        ) {
          return 180;
        } else {
          return 100;
        }
      }

      let col = readColumns(this.state.responseTable);

      // TODO: Make columns deterministic, add translations for headers
      colFormat = col.map((val) => ({
        id: val,
        Header: val,
        accessor: val,
        className: "myCol",
        width: widthCalc(val),
      }));
    }

    return colFormat;
  }

  renderReset() {
    const { selectedQuestions, toggleList, selectedTags } = this.state;
    if (!toggleList) {
      if (selectedTags.length || selectedQuestions.length) {
        return (
          <button onClick={(e) => this.reset(e)} className="btn btn-primary">
            Reset
          </button>
        );
      }
    }
  }

  // Reset state, question and tag list UI
  reset() {
    // reset checkboxes
    document
      .querySelectorAll("input[type=checkbox]")
      .forEach((el) => (el.checked = false));

    // disable question list
    this.toggleList(true);

    this.setState(
      {
        selectedQuestions: [],
        selectedTags: [],
      },
      () => this.refreshResponses()
    );
  }

  toggleUnsubmitted = () => {
    this.setState(
      {
        includeUnsubmitted: !this.state.includeUnsubmitted,
      },
      () => this.refreshResponses()
    );
  };

  handleChange = (event) => {
    const value = event.target.value;
    this.setState({
      newReviewerEmail: value,
      reviewerAssignError: "",
      reviewerAssignSuccess: "",
    });
  };

  assignReviewer = () => {
    reviewService
      .assignResponsesToReviewer(
        this.props.event.id,
        this.state.selectedResponseIds,
        this.state.newReviewerEmail
      )
      .then((response) => {
        this.setState({
          reviewerAssignError: response.error,
          newReviewerEmail: response.error ? this.state.newReviewerEmail : "",
          numReviewsAssigned: response.error
            ? 0
            : this.state.selectedResponseIds.length,
          assignedReviewerEmail: response.error
            ? ""
            : this.state.newReviewerEmail,
          reviewerAssignSuccess: !response.error,
        });
        if (!response.error) {
          this.refreshResponses();
        }
      });
  };

  render() {
    // Translation
    const t = this.props.t;

    // State values
    const {
      questions,
      toggleList,
      responseTable,
      btnUpdate,
      tags,
      selectedTags,
      selectedQuestions,
      error,
      isLoading,
      numReviewsAssigned,
      assignedReviewerEmail,
      reviewerAssignError,
      newReviewerEmail,
      reviewerAssignSuccess,
    } = this.state;

    if (error) {
      return (
        <div className={"alert alert-danger alert-container"}>{error}</div>
      );
    }

    if (isLoading) {
      return <Loading />;
    }

    // Generate Col
    const columns = this.generateCols();
    const renderReset = this.renderReset();

    return (
      <section className="response-list-wrapper">
        <div
          className={
            responseTable ? "question-wrapper wide" : "question-wrapper"
          }
        >
          {/*Heading*/}
          <h2
            className={
              toggleList || responseTable ? "heading short" : "heading"
            }
          >
            {t("Response List")}
          </h2>
          {/*CheckBox*/}
          <div className="checkbox-top">
            <input
              onClick={(e) => this.toggleUnsubmitted()}
              className="form-check-input input"
              type="checkbox"
              value=""
              id="defaultCheck1"
            />
            <label id="label" className="label-top" htmlFor="defaultCheck1">
              {t("Include un-submitted")}
            </label>
          </div>

          {/* Wrapper for drop down lists */}
          <div className="lists-wrapper">
            {/*Tags Dropdown*/}
            <div className="tags">
              {toggleList == "tag" ? (
                <button
                  onClick={(e) => this.refreshResponses()}
                  type="button"
                  className="btn btn-success"
                >
                  {t("Update")}
                </button>
              ) : (
                <button
                  onClick={(e) => this.toggleList(toggleList, "tag")}
                  className={
                    toggleList == "question" ? "btn tag hide" : "btn tag"
                  }
                  type="button"
                  aria-haspopup="true"
                  aria-expanded="false"
                >
                  {t("Tags")}
                </button>
              )}
            </div>

            {/*Questions DropDown*/}
            <div className="questions">
              {toggleList == "question" ? (
                <button
                  onClick={(e) => this.refreshResponses()}
                  type="button"
                  className={
                    toggleList == "tag"
                      ? "btn btn-success hide"
                      : "btn btn-success"
                  }
                >
                  {t("Update")}
                </button>
              ) : (
                <button
                  onClick={(e) => this.toggleList(toggleList, "question")}
                  className={
                    toggleList == "tag"
                      ? "btn btn-secondary hide"
                      : "btn btn-secondary"
                  }
                  type="button"
                  aria-haspopup="true"
                  aria-expanded="false"
                >
                  {t("Questions")}
                </button>
              )}

              {/* Reset Button */}
              {renderReset}

              {/*Update Table*/}
              {toggleList == "question" && questions.length && (
                <span style={{ marginLeft: "5px", color: "grey" }}>
                  {questions.length} {t("questions")}
                </span>
              )}
            </div>

            {/*Pills*/}
            <div class="pills">
              {selectedTags &&
                selectedTags.map((val) => {
                  return (
                    <span
                      onClick={(e) => this.deletePill(val)}
                      className="badge badge-primary"
                    >
                      {val} <i className="far fa-trash-alt"></i>
                    </span>
                  );
                })}
            </div>
          </div>

          {/* List Section */}
          <div className="list-section">
            {/*Tag List*/}
            <div className={toggleList == "tag" ? "tag-list show" : "tag-list"}>
              {tags &&
                tags.map((val) => {
                  return (
                    <div
                      className={
                        selectedTags.includes(val.name)
                          ? "tag-item hide"
                          : "tag-item"
                      }
                      key={val.id}
                    >
                      <button
                        className="btn tags"
                        onClick={(e) => this.tagSelector(val.name)}
                      >
                        {val.name}
                      </button>
                    </div>
                  );
                })}
              {/* Update Button */}
            </div>

            {/* List Questions */}
            <div
              className={
                toggleList == "question"
                  ? "question-list show"
                  : "question-list "
              }
            >
              {questions &&
                questions.length &&
                questions.map((val) => {
                  return (
                    <div
                      className={
                        selectedQuestions.includes(val.question_id)
                          ? "questions-item hide"
                          : "questions-item"
                      }
                      key={val.headline + "" + val.value}
                    >
                      <input
                        onClick={(e) => this.questionSelector(val.question_id)}
                        className="question-list-inputs"
                        type="checkbox"
                        value=""
                        id={val.question_id}
                      />
                      <label
                        style={{ marginLeft: "5px" }}
                        className="form-check-label"
                        htmlFor={val.question_id}
                      >
                        {val.headline}
                      </label>
                    </div>
                  );
                })}
            </div>
          </div>
        </div>

        <div className="react-table">
          {/* Response Table */}
          {!toggleList && (
            <ReactTable
              className="ReactTable"
              data={responseTable ? responseTable : []}
              columns={columns}
              minRows={0}
            />
          )}
        </div>

        <div className="review-assign-container">
          <FormTextBox
            id={"newReviewEmail"}
            name={"newReviewEmail"}
            label={t("Assign Reviewer (they must already have an account)")}
            placeholder={t("Email")}
            onChange={this.handleChange}
            value={newReviewerEmail}
            key={"i_newReviewEmail"}
          />

          <button
            class="btn btn-primary float-right"
            onClick={() => {
              this.assignReviewer();
            }}
            disabled={!newReviewerEmail}
          >
            {t("Assign")}
          </button>

          {reviewerAssignError && (
            <span className="alert alert-danger">
              {JSON.stringify(this.state.reviewerAssignError)}
            </span>
          )}

          {reviewerAssignSuccess && (
            <span className="alert alert-success">
              <Trans i18nKey="reviewsAssigned">
                Assigned {{ numReviewsAssigned }} reviews to{" "}
                {{ assignedReviewerEmail }}
              </Trans>
            </span>
          )}
        </div>
      </section>
    );
  }
}

export default withTranslation()(ResponseListForm);
