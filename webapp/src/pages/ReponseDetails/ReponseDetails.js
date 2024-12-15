import React, { Component } from "react";
import { withRouter } from "react-router";
import { Link } from "react-router-dom";
import { applicationFormService } from "../../services/applicationForm";
import Loading from "../../components/Loading";
import { withTranslation } from "react-i18next";
import AnswerValue from "../../components/answerValue";
import { eventService } from "../../services/events";
import moment from "moment";
import "./ResponseDetails.css";

class ReponseDetails extends Component {
  constructor(props) {
    super(props);
    this.state = {
      applicationData: null,
      applicationForm: null,
      all_responses: null,
      isLoading: true,
      outcome: null,
      error: false,
    };
  }

  componentDidMount() {
    const eventId = this.props.event ? this.props.event.id : 0;
    Promise.all([
      applicationFormService.getForEvent(eventId),
      applicationFormService.getResponse(eventId),
      eventService.getEvent(eventId),
    ]).then((responses) => {
      this.setState({
        applicationForm: responses[0].formSpec,
        all_responses: responses[1].response,
        applicationData: responses[1].response.find(
          (item) => item.id === parseInt(this.props.match.params.id)
        ),
        isLoading: false,
        error: responses[0].error || responses[1].error || responses[2].error,
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

  outcomeStatus() {
    const data = this.state.applicationData;

    if (data.outcome) {
      const badgeClass =
        data.outcome === "ACCEPTED"
          ? "badge-success"
          : data.outcome === "REJECTED"
          ? "badge-danger"
          : "badge-warning";

      return (
        <span>
          <span className={`badge badge-pill ${badgeClass}`}>
            {data.outcome}
          </span>{" "}
        </span>
      );
    } else {
      return (
        <span>
          <span className={`badge badge-pill badge-secondary`}>
            {"Pending ..."}
          </span>
        </span>
      );
    }
  }

  getChainById = (data, id) => {
    const elementMap = data.reduce((map, element) => {
      map[element.id] = element;
      return map;
    }, {});

    function getChain(element, visited = new Set()) {
      if (!element || visited.has(element.id)) return [];
      visited.add(element.id);

      const chain = [element];
      if (element.parent_id !== null && elementMap[element.parent_id]) {
        chain.push(...getChain(elementMap[element.parent_id], visited));
      }
      data.forEach((child) => {
        if (child.parent_id === element.id) {
          chain.push(...getChain(child, visited));
        }
      });

      return chain;
    }

    if (!elementMap[id]) {
      return [];
    }

    const result = getChain(elementMap[id]);
    result.sort((a, b) => a.id - b.id);

    return result;
  };

  hasAcceptedStatus = (chain) => {
    return chain.some((element) => element.outcome === "ACCEPTED");
  };

  getLastId = (data) => {
    if (!data || data.length === 0) return null;
    let lastId = null;
    data.forEach((element) => {
      if (lastId === null || element.id > lastId) {
        lastId = element.id;
      }
    });
    return lastId;
  };
  getSubmissionList = (applications) => {
    if (!applications || applications.length === 0) {
      return <p>No submissions available.</p>;
    }

    return (
      <div id="application-list" className="application-list">
        <h3> Related Submissions</h3>
        <ul className="application-list_items">
          {applications.map((application) => (
            <li key={application.id} className="application-list_item">
              <a
                href={`/${this.props.event.key}/responseDetails/${application.id}`}
                className="application-list_link"
              >
                {this.props.t(`Submission ${application.id}`)}
              </a>
            </li>
          ))}
        </ul>
      </div>
    );
  };

  render() {
    const { applicationData, isLoading, error, all_responses } = this.state;
    if (isLoading) {
      return <Loading />;
    }
    const result = this.getChainById(all_responses, this.props.match.params.id);
    return (
      <div className="table-wrapper response-page">
        {error && (
          <div className="alert alert-danger" role="alert">
            <p>{JSON.stringify(error)}</p>
          </div>
        )}

        <div className="headings-lower">
          <div className="user-details right">
            <label>{this.props.t("Application Status")}</label>{" "}
            <p>{this.applicationStatus()}</p>
            <label>{this.props.t("Application Outcome")}</label>{" "}
            <p>{this.outcomeStatus()}</p>
          </div>
        </div>

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
              {
                <button
                  className="btn btn-primary shift_button"
                  onClick={() =>
                    (window.location.href = `/${
                      this.props.event.key
                    }/apply/new/${this.getLastId(result)}`)
                  }
                  disabled={this.hasAcceptedStatus(result)}
                >
                  {this.props.t("New submission")}
                </button>
              }
            </div>
          </div>
        )}
        <div className="response-details">
          {this.getSubmissionList(
            result.filter(
              (element) => element.id !== parseInt(this.props.match.params.id)
            )
          )}
        </div>
      </div>
    );
  }
}

export default withRouter(withTranslation()(ReponseDetails));