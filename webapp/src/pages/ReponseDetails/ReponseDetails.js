import React, { Component } from "react";
import { withRouter } from "react-router";
import { Link } from "react-router-dom";
import { applicationFormService } from "../../services/applicationForm";

import Loading from "../../components/Loading";
import _ from "lodash";
import { withTranslation } from "react-i18next";
import AnswerValue from "../../components/answerValue";
import { eventService } from "../../services/events";

class ReponseDetails extends Component {
  constructor(props) {
    super(props);
    this.state = {
      applicationData: null,
      applicationForm: null,
      isLoading: true,
    };
  }

  componentDidMount() {
    const eventId = this.props.event ? this.props.event.id : 0;
    Promise.all([
      applicationFormService.getForEvent(eventId),
      applicationFormService.getResponse(eventId),
      eventService.getEvent(eventId),
    ]).then((responses) => {
      console.log(responses);
      this.setState({
        applicationForm: responses[0].formSpec,
        applicationData: responses[1].response.find(
          (item) => item.id === parseInt(this.props.match.params.id)
        ),
        isLoading: false,
      });
    });
  }

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
  goBack() {
    this.props.history.goBack();
  }

  render() {
    const { applicationData, isLoading } = this.state;
    if (isLoading) {
      return <Loading />;
    }

    return (
      <div className="table-wrapper response-page">
        {/* API Error
                {error &&
                    <div className="alert alert-danger" role="alert">
                        <p>{JSON.stringify(error)}</p>
                    </div>
                }

                {this.renderReviewerModal()}
                {this.renderDeleteTagModal()}
                {this.renderDeleteReviewerModal()} */}

        {/* Headings */}
        {/* {applicationData &&
                    <div className="headings-lower">
                        <div className="user-details">
                            <h2>{applicationData.user_title} {applicationData.firstname} {applicationData.lastname}</h2>
                            <p>{t("Language")}: {applicationData.language}</p>
                            <div className="tags">
                                {this.renderTags()}
                                <span className="btn badge badge-add" onClick={() => this.setTagSelectorVisible()}>{t("Add tag")}</span>

                            </div>

                        </div>

                        {/* User details Right Tab */}
        {/* <div>
                            <div className="user-details right">
                                <label>{t('Application Status')}</label> <p>{this.applicationStatus()}</p>
                                <label>{t('Application Outcome')}</label> <p>{this.outcomeStatus()}</p>
                                <button className="btn btn-secondary" onClick={((e) => this.goBack(e))}>{t('Go Back')}</button>
                            </div>

                        </div>
                    </div>
                } */}

        {/*Response Data*/}
        {applicationData && (
          <div className="response-details">

            {this.renderSections()}
            <br />
            <div>
              <button
                className="btn btn-secondary"
                onClick={(e) => this.goBack(e)}
              >
                {this.props.t("Go Back")}
              </button>
            </div>

          </div>
        )}
      </div>
    );
  }
}

export default withRouter(withTranslation()(ReponseDetails));
