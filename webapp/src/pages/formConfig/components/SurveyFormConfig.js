import React, { Component } from "react";
import { withTranslation } from "react-i18next";
import { formServices } from "../../../services/form/form.service";
import { formConfigService } from "../../../services/formConfig/formConfig.service";

// <input type=datetime-local> works in "YYYY-MM-DDTHH:MM" local wall-clock values,
// with no timezone of its own — it is deliberately reused here as-is to represent
// a moment in the *event's* timezone rather than the browser's.
function toDatetimeLocalValue(isoString) {
    if (!isoString) {
        return "";
    }
    return isoString.slice(0, 16);
}

class SurveyFormConfig extends Component {
    constructor(props) {
        super(props);
        this.state = {
            forms: [],
            selectedFormId: props.surveyFormId || "",
            selectedSurveyOpen: toDatetimeLocalValue(props.surveyOpen),
            isLoading: true,
            isSaving: false,
            error: null,
            saved: false
        };
    }

    componentDidMount() {
        this.loadForms();
    }

    componentDidUpdate(prevProps) {
        if (prevProps.surveyFormId !== this.props.surveyFormId) {
            this.setState({ selectedFormId: this.props.surveyFormId || "" });
        }
        if (prevProps.surveyOpen !== this.props.surveyOpen) {
            this.setState({ selectedSurveyOpen: toDatetimeLocalValue(this.props.surveyOpen) });
        }
    }

    loadForms = () => {
        formServices.getFormList(this.props.eventId).then(function(result) {
            this.setState({
                forms: result.forms || [],
                isLoading: false
            });
        }.bind(this));
    }

    handleFormChange = (e) => {
        this.setState({ selectedFormId: e.target.value, saved: false });
    }

    handleSurveyOpenChange = (e) => {
        this.setState({ selectedSurveyOpen: e.target.value, saved: false });
    }

    handleSave = () => {
        var formId = this.state.selectedFormId ? parseInt(this.state.selectedFormId, 10) : null;
        var surveyOpen = this.state.selectedSurveyOpen || null;
        this.setState({ isSaving: true, error: null, saved: false });
        formConfigService.assignSurveyForm(this.props.eventId, formId, surveyOpen).then(function(result) {
            if (result.error) {
                this.setState({ isSaving: false, error: result.error });
            } else {
                this.setState({ isSaving: false, saved: true });
                if (this.props.onSaved) {
                    this.props.onSaved();
                }
            }
        }.bind(this));
    }

    formName = (form) => {
        var t = this.props.t;
        if (!form.name) {
            return t('Untitled Form');
        }
        var translatedName = form.name.en || Object.keys(form.name).map(function(lang) { return form.name[lang]; }).filter(Boolean)[0];
        return translatedName || t('Untitled Form');
    }

    render() {
        var t = this.props.t;
        var forms = this.state.forms;
        var hasChanges = String(this.state.selectedFormId || "") !== String(this.props.surveyFormId || "")
            || this.state.selectedSurveyOpen !== toDatetimeLocalValue(this.props.surveyOpen);

        return (
            <div className="bg-white rounded-2xl shadow-sm border border-border p-6 space-y-4">
                <div className="border-b border-border/50 pb-4">
                    <h2 className="text-lg font-semibold text-foreground/90">{t('Post-Event Survey')}</h2>
                    <p className="text-sm text-muted-foreground mt-1">
                        {t('Attendees will be prompted to fill in this form once it becomes available.')}
                    </p>
                </div>

                {this.state.error && (
                    <div className="bg-error/10 text-error border border-error/20 p-3 rounded-xl text-sm">
                        {this.state.error}
                    </div>
                )}

                <div className="space-y-3">
                    <div>
                        <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                            {t('Survey Form')}
                        </label>
                        <select
                            className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-white"
                            value={this.state.selectedFormId || ""}
                            onChange={this.handleFormChange}
                            disabled={this.state.isLoading}
                        >
                            <option value="">{t('No survey form selected')}</option>
                            {forms.map(function(form) {
                                return (
                                    <option key={form.id} value={form.id}>{this.formName(form)}</option>
                                );
                            }.bind(this))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">
                            {t('Available From')} {this.props.eventTimezone ? `(${this.props.eventTimezone})` : ''}
                        </label>
                        <input
                            type="datetime-local"
                            className="w-full sm:w-auto border border-border rounded-lg px-3 py-2 text-sm bg-white"
                            value={this.state.selectedSurveyOpen}
                            onChange={this.handleSurveyOpenChange}
                        />
                        <p className="text-xs text-muted-foreground mt-1">
                            {t('Attendees will only see the survey prompt from this date and time, in the event\'s own timezone.')}
                        </p>
                    </div>

                    <div>
                        <button
                            type="button"
                            className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-semibold bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50"
                            onClick={this.handleSave}
                            disabled={!hasChanges || this.state.isSaving}
                        >
                            {this.state.isSaving ? t('Saving...') : t('Save')}
                        </button>
                    </div>
                </div>

                {this.state.saved && (
                    <p className="text-sm text-success">{t('Survey form updated.')}</p>
                )}
            </div>
        );
    }
}

export default withTranslation()(SurveyFormConfig);
