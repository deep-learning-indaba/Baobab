import React, { Component } from "react";
import { withTranslation } from "react-i18next";
import { formResponseService } from "../../../services/formResponse";

class FormResponseListComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      responses: [],
      loading: true,
      error: null,
      pagination: {
        page: 1,
        per_page: 25,
        total: 0,
        pages: 0
      },
      filters: {
        is_submitted: '',
        is_withdrawn: '',
        email: '',
        name: ''
      }
    };
  }

  componentDidMount() {
    this.loadResponses();
  }

  loadResponses = async () => {
    this.setState({ loading: true, error: null });

    const formId = this.props.match.params.formId;
    const eventId = this.props.event ? this.props.event.id : null;

    if (!eventId) {
      this.setState({ 
        loading: false, 
        error: this.props.t("Event information not available") 
      });
      return;
    }

    const filters = {
      page: this.state.pagination.page,
      per_page: this.state.pagination.per_page,
      ...this.state.filters
    };

    const result = await formResponseService.getResponseListAdmin(eventId, formId, filters);

    if (result.error) {
      this.setState({ loading: false, error: result.error });
    } else {
      this.setState({
        responses: result.data.responses || [],
        pagination: result.data.pagination || this.state.pagination,
        loading: false
      });
    }
  };

  handlePageChange = (newPage) => {
    this.setState(
      prevState => ({
        pagination: { ...prevState.pagination, page: newPage }
      }),
      () => this.loadResponses()
    );
  };

  handleFilterChange = (filterName, value) => {
    this.setState(
      prevState => ({
        filters: { ...prevState.filters, [filterName]: value },
        pagination: { ...prevState.pagination, page: 1 }
      }),
      () => this.loadResponses()
    );
  };

  handleSearchSubmit = (e) => {
    e.preventDefault();
    this.setState(
      prevState => ({
        pagination: { ...prevState.pagination, page: 1 }
      }),
      () => this.loadResponses()
    );
  };

  handleViewResponse = (responseId) => {
    const formId = this.props.match.params.formId;
    const eventKey = this.props.event ? this.props.event.key : null;
    this.props.history.push(`/${eventKey}/form-responses/${formId}/${responseId}`);
  };

  handleBackToForms = () => {
    const eventKey = this.props.event ? this.props.event.key : null;
    this.props.history.push(`/${eventKey}/formManagement`);
  };

  render() {
    const { t } = this.props;
    const { responses, loading, error, pagination, filters } = this.state;

    if (loading && responses.length === 0) {
      return (
        <div className="response-list-page">
          <div className="loading-container">
            <div className="spinner-border" role="status">
              <span className="sr-only">{t("Loading...")}</span>
            </div>
            <p>{t("Loading responses...")}</p>
          </div>
        </div>
      );
    }

    if (error && responses.length === 0) {
      return (
        <div className="response-list-page">
          <div className="error-container">
            <div className="alert alert-danger">
              <i className="fas fa-exclamation-triangle"></i>
              <h3>{t("Error")}</h3>
              <p>{error}</p>
              <button className="btn btn-primary" onClick={this.handleBackToForms}>
                {t("Back to Forms")}
              </button>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="response-list-page">
        <div className="response-list-header">
          <div className="header-left">
            <button className="btn-back" onClick={this.handleBackToForms}>
              <i className="fas fa-arrow-left"></i>
              {t("Back to Forms")}
            </button>
            <h1>{t("Form Responses")}</h1>
          </div>
        </div>

        <div className="response-list-filters">
          <form onSubmit={this.handleSearchSubmit} className="filters-form">
            <div className="filter-group">
              <label>{t("Search by Email")}</label>
              <input
                type="text"
                className="form-control"
                placeholder={t("Enter email")}
                value={filters.email}
                onChange={(e) => this.handleFilterChange('email', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label>{t("Search by Name")}</label>
              <input
                type="text"
                className="form-control"
                placeholder={t("Enter name")}
                value={filters.name}
                onChange={(e) => this.handleFilterChange('name', e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label>{t("Status")}</label>
              <select
                className="form-control"
                value={filters.is_submitted}
                onChange={(e) => this.handleFilterChange('is_submitted', e.target.value)}
              >
                <option value="">{t("All")}</option>
                <option value="true">{t("Submitted")}</option>
                <option value="false">{t("Draft")}</option>
              </select>
            </div>

            <div className="filter-group">
              <label>{t("Withdrawn")}</label>
              <select
                className="form-control"
                value={filters.is_withdrawn}
                onChange={(e) => this.handleFilterChange('is_withdrawn', e.target.value)}
              >
                <option value="">{t("All")}</option>
                <option value="true">{t("Yes")}</option>
                <option value="false">{t("No")}</option>
              </select>
            </div>

            <div className="filter-actions">
              <button type="submit" className="btn btn-primary">
                <i className="fas fa-search"></i>
                {t("Search")}
              </button>
            </div>
          </form>
        </div>

        {responses.length === 0 ? (
          <div className="empty-state">
            <i className="fas fa-inbox"></i>
            <h3>{t("No responses found")}</h3>
            <p>{t("No responses match your current filters.")}</p>
          </div>
        ) : (
          <>
            <div className="response-list-table">
              <table className="table">
                <thead>
                  <tr>
                    <th>{t("User")}</th>
                    <th>{t("Email")}</th>
                    <th>{t("Status")}</th>
                    <th>{t("Started")}</th>
                    <th>{t("Submitted")}</th>
                    <th>{t("Answers")}</th>
                    <th>{t("Actions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {responses.map(response => (
                    <tr key={response.id} className={response.is_withdrawn ? 'withdrawn-row' : ''}>
                      <td>
                        <div className="user-name">
                          {response.user.user_title} {response.user.firstname} {response.user.lastname}
                        </div>
                      </td>
                      <td>{response.user.email}</td>
                      <td>
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
                      </td>
                      <td>
                        {response.started_timestamp ? 
                          new Date(response.started_timestamp).toLocaleDateString() : 
                          '-'
                        }
                      </td>
                      <td>
                        {response.submitted_timestamp ? 
                          new Date(response.submitted_timestamp).toLocaleDateString() : 
                          '-'
                        }
                      </td>
                      <td>
                        <span className="answer-count">{response.answer_count}</span>
                      </td>
                      <td>
                        <button 
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => this.handleViewResponse(response.id)}
                        >
                          <i className="fas fa-eye"></i>
                          {t("View")}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {pagination.pages > 1 && (
              <div className="pagination-controls">
                <button
                  className="btn btn-outline-secondary"
                  disabled={pagination.page === 1}
                  onClick={() => this.handlePageChange(pagination.page - 1)}
                >
                  <i className="fas fa-chevron-left"></i>
                  {t("Previous")}
                </button>
                
                <span className="pagination-info">
                  {t("Page {{current}} of {{total}}", { 
                    current: pagination.page, 
                    total: pagination.pages 
                  })}
                  {" "}({t("{{count}} total responses", { count: pagination.total })})
                </span>

                <button
                  className="btn btn-outline-secondary"
                  disabled={pagination.page === pagination.pages}
                  onClick={() => this.handlePageChange(pagination.page + 1)}
                >
                  {t("Next")}
                  <i className="fas fa-chevron-right"></i>
                </button>
              </div>
            )}
          </>
        )}
      </div>
    );
  }
}

export default withTranslation()(FormResponseListComponent);
