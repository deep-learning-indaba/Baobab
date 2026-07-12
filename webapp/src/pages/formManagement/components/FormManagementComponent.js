import React, { Component } from "react";
import { formServices } from "../../../services/form/form.service";
import { withRouter } from "react-router-dom";
import { withTranslation } from "react-i18next";

class FormManagementComponent extends Component {
  constructor(props) {
    super(props);
    this.state = {
      forms: [],
      loading: true,
      error: null
    };
  }

  componentDidMount() {
    this.loadForms();
  }

  loadForms = () => {
    this.setState({ loading: true, error: null });

    formServices.getFormList()
      .then(response => {
        if (response.error) {
          this.setState({
            error: response.error,
            loading: false
          });
        } else {
          this.setState({
            forms: response.forms || [],
            loading: false
          });
        }
      })
      .catch(error => {
        this.setState({
          error: error.message || "Failed to load forms",
          loading: false
        });
      });
  };

  handleAddNew = () => {
    const eventKey = this.props.event ? this.props.event.key : this.props.match.params.eventKey;
    this.props.history.push(`/${eventKey}/forms/new`);
  };

  handleEdit = (formId) => {
    const eventKey = this.props.event ? this.props.event.key : this.props.match.params.eventKey;
    this.props.history.push(`/${eventKey}/forms/${formId}/edit`);
  };

  handleView = (formId) => {
    const eventKey = this.props.event ? this.props.event.key : this.props.match.params.eventKey;
    this.props.history.push(`/${eventKey}/forms/${formId}`);
  };

  handlePreview = (formId) => {
    const eventKey = this.props.event ? this.props.event.key : this.props.match.params.eventKey;
    window.open(`/${eventKey}/forms/${formId}/preview`, '_blank');
  };

  handleViewResponses = (formId) => {
    const eventKey = this.props.event ? this.props.event.key : this.props.match.params.eventKey;
    this.props.history.push(`/${eventKey}/form-responses/${formId}`);
  };

  getFormName = (form) => {
    if (!form.name) return this.props.t("Untitled Form");
    if (typeof form.name === 'object') {
      return form.name.en || form.name[Object.keys(form.name)[0]] || this.props.t("Untitled Form");
    }
    return form.name;
  };

  getFormDescription = (form) => {
    if (!form.description) return "";
    if (typeof form.description === 'object') {
      return form.description.en || form.description[Object.keys(form.description)[0]] || "";
    }
    return form.description;
  };

  render() {
    const { forms, loading, error } = this.state;
    const { t } = this.props;

    if (loading) {
      return (
        <div className="form-management">
          <div className="loading-container">
            <div className="spinner-border text-primary" role="status">
              <span className="sr-only">{t("Loading...")}</span>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="form-management">
        <div className="form-management-header">
          <h1>{t("Forms Management")}</h1>
          <button className="add-form-btn" onClick={this.handleAddNew}>
            <i className="fas fa-plus"></i>
            {t("Add New Form")}
          </button>
        </div>

        {error && (
          <div className="error-container">
            <i className="fas fa-exclamation-triangle"></i> {error}
          </div>
        )}

        {forms.length === 0 ? (
          <div className="empty-state">
            <i className="fas fa-file-alt"></i>
            <h3>{t("No forms found")}</h3>
            <p>{t("Get started by creating your first form")}</p>
            <button className="add-form-btn" onClick={this.handleAddNew} style={{ marginTop: "1rem" }}>
              <i className="fas fa-plus"></i>
              {t("Add New Form")}
            </button>
          </div>
        ) : (
          <div className="forms-list">
            {forms.map((form) => (
              <div key={form.id} className="form-card">
                <div className="form-card-header">
                  <h2 className="form-card-title">{this.getFormName(form)}</h2>
                  <div className="form-card-badges">
                    {form.is_active ? (
                      <span className="badge badge-active">{t("Active")}</span>
                    ) : (
                      <span className="badge badge-inactive">{t("Inactive")}</span>
                    )}
                    {form.is_open ? (
                      <span className="badge badge-open">{t("Open")}</span>
                    ) : (
                      <span className="badge badge-closed">{t("Closed")}</span>
                    )}
                  </div>
                </div>

                {this.getFormDescription(form) && (
                  <p className="form-card-description">
                    {this.getFormDescription(form)}
                  </p>
                )}

                <div className="form-card-meta">
                  <div className="form-card-meta-item">
                    <i className="fas fa-calendar"></i>
                    <span>
                      {t("Created")}: {new Date(form.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {form.updated_at && (
                    <div className="form-card-meta-item">
                      <i className="fas fa-clock"></i>
                      <span>
                        {t("Updated")}: {new Date(form.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>

                <div className="form-card-actions">
                  <button className="btn-edit" onClick={() => this.handleEdit(form.id)}>
                    <i className="fas fa-edit"></i> {t("Edit")}
                  </button>
                  <button className="btn-preview" onClick={() => this.handlePreview(form.id)}>
                    <i className="fas fa-eye"></i> {t("Preview")}
                  </button>
                  <button className="btn-responses" onClick={() => this.handleViewResponses(form.id)}>
                    <i className="fas fa-list-alt"></i> {t("Responses")}
                  </button>
                  <button className="btn-view" onClick={() => this.handleView(form.id)}>
                    <i className="fas fa-file-alt"></i> {t("View")}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }
}

export default withRouter(withTranslation()(FormManagementComponent));
