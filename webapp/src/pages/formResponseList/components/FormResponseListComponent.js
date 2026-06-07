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

  getFormId() {
    return this.props.formId || (this.props.match && this.props.match.params && this.props.match.params.formId);
  }

  loadResponses = async () => {
    this.setState({ loading: true, error: null });

    const formId = this.getFormId();
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
    const formId = this.getFormId();
    const eventKey = this.props.event ? this.props.event.key : null;
    this.props.history.push(`/${eventKey}/form-responses/${formId}/${responseId}`);
  };

  handleBack = () => {
    if (this.props.formId) {
      // Rendered from /responseList context — go back
      this.props.history.goBack();
    } else {
      const eventKey = this.props.event ? this.props.event.key : null;
      this.props.history.push(`/${eventKey}/formManagement`);
    }
  };

  render() {
    const { t } = this.props;
    const { responses, loading, error, pagination, filters } = this.state;

    if (loading && responses.length === 0) {
      return (
        <div className="flex justify-center items-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      );
    }

    if (error && responses.length === 0) {
      return (
        <div className="max-w-3xl mx-auto pt-8 px-4">
          <div className="bg-error/10 text-error border border-error/20 p-6 rounded-xl text-sm">
            <p className="font-semibold mb-1">{t("Error")}</p>
            <p>{error}</p>
            <button className="mt-4 text-sm font-medium text-primary hover:underline" onClick={this.handleBack}>
              ← {t("Go Back")}
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-6">
        <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <h1 className="font-heading text-2xl font-bold text-foreground">{t("Response List")}</h1>
            {!this.props.formId && (
              <button onClick={this.handleBack}
                      className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline">
                ← {t("Back to Forms")}
              </button>
            )}
          </div>

          <form onSubmit={this.handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-foreground/90">{t("Filter by email")}</label>
              <input
                type="text"
                className="w-full px-3 py-2 rounded-lg border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                placeholder={t("Search")}
                value={filters.email}
                onChange={(e) => this.setState(p => ({ filters: { ...p.filters, email: e.target.value } }))}
              />
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-semibold text-foreground/90">{t("Filter by name")}</label>
              <input
                type="text"
                className="w-full px-3 py-2 rounded-lg border border-border text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                placeholder={t("Search")}
                value={filters.name}
                onChange={(e) => this.setState(p => ({ filters: { ...p.filters, name: e.target.value } }))}
              />
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-semibold text-foreground/90">{t("Status")}</label>
              <select
                className="w-full px-3 py-2 rounded-lg border border-border text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary/30"
                value={filters.is_submitted}
                onChange={(e) => this.handleFilterChange('is_submitted', e.target.value)}
              >
                <option value="">{t("All")}</option>
                <option value="true">{t("Submitted")}</option>
                <option value="false">{t("Draft")}</option>
              </select>
            </div>

            <div className="flex items-end pb-0">
              <button type="submit"
                      className="w-full inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm">
                {t("Search")}
              </button>
            </div>
          </form>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="show_withdrawn"
              className="rounded border-border text-primary focus:ring-primary w-4 h-4 cursor-pointer"
              checked={filters.is_withdrawn === 'true'}
              onChange={e => this.handleFilterChange('is_withdrawn', e.target.checked ? 'true' : '')}
            />
            <label htmlFor="show_withdrawn" className="text-sm font-medium text-foreground cursor-pointer select-none">
              {t("Show withdrawn only")}
            </label>
          </div>

          {responses.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              <p className="text-sm">{t("No responses match your current filters.")}</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left font-bold py-2 pr-4 text-foreground/80">{t("Name")}</th>
                      <th className="text-left font-bold py-2 pr-4 text-foreground/80">{t("Email")}</th>
                      <th className="text-left font-bold py-2 pr-4 text-foreground/80">{t("Status")}</th>
                      <th className="text-left font-bold py-2 pr-4 text-foreground/80">{t("Started")}</th>
                      <th className="text-left font-bold py-2 pr-4 text-foreground/80">{t("Submitted")}</th>
                      <th className="text-left font-bold py-2 pr-4 text-foreground/80">{t("Answers")}</th>
                      <th className="py-2"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {responses.map(response => (
                      <tr key={response.id}
                          className={`border-b border-border/40 hover:bg-surface-low/50 transition-colors ${response.is_withdrawn ? 'opacity-60' : ''}`}>
                        <td className="py-2 pr-4 font-medium">
                          {response.user.user_title} {response.user.firstname} {response.user.lastname}
                        </td>
                        <td className="py-2 pr-4 text-muted-foreground">{response.user.email}</td>
                        <td className="py-2 pr-4">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${
                            response.is_withdrawn ? 'bg-error/10 text-error border-error/20' :
                            response.is_submitted ? 'bg-green-50 text-green-700 border-green-200' :
                            'bg-amber-50 text-amber-700 border-amber-200'
                          }`}>
                            {response.is_withdrawn ? t("Withdrawn") :
                             response.is_submitted ? t("Submitted") : t("Draft")}
                          </span>
                        </td>
                        <td className="py-2 pr-4 text-muted-foreground">
                          {response.started_timestamp ? new Date(response.started_timestamp).toLocaleDateString() : '-'}
                        </td>
                        <td className="py-2 pr-4 text-muted-foreground">
                          {response.submitted_timestamp ? new Date(response.submitted_timestamp).toLocaleDateString() : '-'}
                        </td>
                        <td className="py-2 pr-4 text-muted-foreground">{response.answer_count}</td>
                        <td className="py-2">
                          <button
                            onClick={() => this.handleViewResponse(response.id)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold border border-primary/30 text-primary hover:bg-primary/5 transition-colors"
                          >
                            {t("View")}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {pagination.pages > 1 && (
                <div className="flex items-center justify-between pt-4 border-t border-border/40">
                  <button
                    className="inline-flex items-center gap-1 px-4 py-2 rounded-lg text-sm font-semibold border border-border text-foreground hover:bg-surface-high transition-colors disabled:opacity-40"
                    disabled={pagination.page === 1}
                    onClick={() => this.handlePageChange(pagination.page - 1)}
                  >
                    ← {t("Previous")}
                  </button>
                  <span className="text-sm text-muted-foreground">
                    {t("Page {{current}} of {{total}}", { current: pagination.page, total: pagination.pages })}
                    {" "}({t("{{count}} total", { count: pagination.total })})
                  </span>
                  <button
                    className="inline-flex items-center gap-1 px-4 py-2 rounded-lg text-sm font-semibold border border-border text-foreground hover:bg-surface-high transition-colors disabled:opacity-40"
                    disabled={pagination.page === pagination.pages}
                    onClick={() => this.handlePageChange(pagination.page + 1)}
                  >
                    {t("Next")} →
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    );
  }
}

export default withTranslation()(FormResponseListComponent);
