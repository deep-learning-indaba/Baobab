import React, { Component } from "react";
import { withTranslation } from "react-i18next";
import { formResponseService } from "../../../services/formResponse";

class FormResponseDetailComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      response: null,
      loading: true,
      error: null
    };
  }

  componentDidMount() {
    this.loadResponse();
  }

  loadResponse = async () => {
    this.setState({ loading: true, error: null });

    const formId = this.props.match.params.formId;
    const responseId = this.props.match.params.responseId;
    const eventId = this.props.event ? this.props.event.id : null;

    if (!eventId) {
      this.setState({ 
        loading: false, 
        error: this.props.t("Event information not available") 
      });
      return;
    }

    const result = await formResponseService.getResponseDetailAdmin(eventId, formId, responseId);

    if (result.error) {
      this.setState({ loading: false, error: result.error });
    } else {
      this.setState({
        response: result.response,
        loading: false
      });
    }
  };

  handleBackToList = () => {
    const formId = this.props.match.params.formId;
    const eventKey = this.props.event ? this.props.event.key : null;
    this.props.history.push(`/${eventKey}/form-responses/${formId}`);
  };

  getAnswerValue = (answer) => {
    if (answer.value === null || answer.value === undefined) return '-';
    
    if (typeof answer.value === 'object') {
      return JSON.stringify(answer.value, null, 2);
    }
    
    return answer.value.toString();
  };

  renderAnswer = (answer) => {
    const value = this.getAnswerValue(answer);
    const isLongText = value.length > 100;
    const isJson = value.startsWith('{') || value.startsWith('[');

    return (
      <div key={answer.id} className="answer-item">
        <div className="answer-meta">
          <span className="question-id">Q{answer.question_id}</span>
          {!answer.is_active && (
            <span className="inactive-badge">{this.props.t("Inactive")}</span>
          )}
        </div>
        <div className={`answer-value ${isLongText || isJson ? 'long-text' : ''}`}>
          {isJson ? (
            <pre>{value}</pre>
          ) : (
            <span>{value}</span>
          )}
        </div>
      </div>
    );
  };

  renderResponseSection = (response, title) => {
    const { t } = this.props;

    return (
      <div className="response-section">
        <div className="section-header">
          <h3>{title}</h3>
          <div className="response-badges">
            <span className={`status-badge ${response.is_submitted ? 'submitted' : 'draft'}`}>
              {response.is_withdrawn ? (
                <>
                  <i className="fas fa-ban"></i> {t("Withdrawn")}
                </>
              ) : response.is_submitted ? (
                <>
                  <i className="fas fa-check-circle"></i> {t("Submitted")}
                </>
              ) : (
                <>
                  <i className="fas fa-edit"></i> {t("Draft")}
                </>
              )}
            </span>
          </div>
        </div>

        <div className="response-info-grid">
          <div className="info-item">
            <span className="info-label">{t("Response ID")}</span>
            <span className="info-value">{response.id}</span>
          </div>
          <div className="info-item">
            <span className="info-label">{t("Form ID")}</span>
            <span className="info-value">{response.form_id}</span>
          </div>
          <div className="info-item">
            <span className="info-label">{t("Language")}</span>
            <span className="info-value">{response.language.toUpperCase()}</span>
          </div>
          <div className="info-item">
            <span className="info-label">{t("Started")}</span>
            <span className="info-value">
              {response.started_timestamp ? 
                new Date(response.started_timestamp).toLocaleString() : 
                '-'
              }
            </span>
          </div>
          {response.submitted_timestamp && (
            <div className="info-item">
              <span className="info-label">{t("Submitted")}</span>
              <span className="info-value">
                {new Date(response.submitted_timestamp).toLocaleString()}
              </span>
            </div>
          )}
          {response.withdrawn_timestamp && (
            <div className="info-item">
              <span className="info-label">{t("Withdrawn")}</span>
              <span className="info-value">
                {new Date(response.withdrawn_timestamp).toLocaleString()}
              </span>
            </div>
          )}
        </div>

        {response.user && (
          <div className="user-info-section">
            <h4>{t("User Information")}</h4>
            <div className="user-info-grid">
              <div className="info-item">
                <span className="info-label">{t("Name")}</span>
                <span className="info-value">
                  {response.user.user_title} {response.user.firstname} {response.user.lastname}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">{t("Email")}</span>
                <span className="info-value">{response.user.email}</span>
              </div>
              <div className="info-item">
                <span className="info-label">{t("User ID")}</span>
                <span className="info-value">{response.user.id}</span>
              </div>
            </div>
          </div>
        )}

        <div className="answers-section">
          <h4>{t("Answers")} ({response.answers ? response.answers.length : 0})</h4>
          {response.answers && response.answers.length > 0 ? (
            <div className="answers-list">
              {response.answers.map(answer => this.renderAnswer(answer))}
            </div>
          ) : (
            <p className="no-answers">{t("No answers provided")}</p>
          )}
        </div>
      </div>
    );
  };

  render() {
    const { t } = this.props;
    const { response, loading, error } = this.state;

    if (loading) {
      return (
        <div className="response-detail-page">
          <div className="loading-container">
            <div className="spinner-border" role="status">
              <span className="sr-only">{t("Loading...")}</span>
            </div>
            <p>{t("Loading response details...")}</p>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="response-detail-page">
          <div className="error-container">
            <div className="alert alert-danger">
              <i className="fas fa-exclamation-triangle"></i>
              <h3>{t("Error")}</h3>
              <p>{error}</p>
              <button className="btn btn-primary" onClick={this.handleBackToList}>
                {t("Back to Response List")}
              </button>
            </div>
          </div>
        </div>
      );
    }

    if (!response) {
      return (
        <div className="response-detail-page">
          <div className="error-container">
            <div className="alert alert-warning">
              <i className="fas fa-exclamation-circle"></i>
              <h3>{t("Response Not Found")}</h3>
              <p>{t("The requested response could not be found.")}</p>
              <button className="btn btn-primary" onClick={this.handleBackToList}>
                {t("Back to Response List")}
              </button>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="response-detail-page">
        <div className="response-detail-header">
          <button className="btn-back" onClick={this.handleBackToList}>
            <i className="fas fa-arrow-left"></i>
            {t("Back to Response List")}
          </button>
          <h1>{t("Response Details")}</h1>
        </div>

        <div className="response-detail-content">
          {this.renderResponseSection(response, t("Primary Response"))}

          {response.linked_response && (
            <div className="linked-response-container">
              <div className="linked-response-header">
                <i className="fas fa-link"></i>
                <h2>{t("Linked Response")}</h2>
              </div>
              {this.renderResponseSection(response.linked_response, t("Linked Form Response"))}
            </div>
          )}
        </div>
      </div>
    );
  }
}

export default withTranslation()(FormResponseDetailComponent);
