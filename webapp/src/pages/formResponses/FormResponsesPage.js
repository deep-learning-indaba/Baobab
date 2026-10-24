import React, { Component } from "react";
import { withTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { formResponseService } from "../../services/formResponse";

class FormResponsesPage extends Component {
    constructor(props) {
        super(props);
        this.state = {
            forms: [],
            isLoading: true,
            error: null
        };
    }

    componentDidMount() {
        this.loadForms();
    }

    loadForms = () => {
        var event = this.props.event;
        if (!event) {
            this.setState({ isLoading: false, error: this.props.t('Event information not available') });
            return;
        }
        var language = (this.props.i18n && this.props.i18n.language) || 'en';
        formResponseService.getFormResponsesSummary(event.id, language).then(function(result) {
            if (result.error) {
                this.setState({ error: result.error, isLoading: false });
            } else {
                this.setState({ forms: result.forms, isLoading: false });
            }
        }.bind(this));
    }

    formTypeLabel(form) {
        var t = this.props.t;
        if (form.is_survey) return t('Survey');
        switch (form.form_type) {
            case 'application':
                return t('Application Form');
            case 'review':
                return t('Review Form') + ' · ' + t('Stage {{stage}}', { stage: form.stage || 1 });
            case 'registration':
                return t('Registration Form');
            default:
                return t('Other Form');
        }
    }

    render() {
        var t = this.props.t;
        var forms = this.state.forms;
        var eventKey = this.props.eventKey;

        if (this.state.isLoading) {
            return (
                <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            );
        }

        if (this.state.error) {
            return (
                <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
                    {this.state.error}
                </div>
            );
        }

        return (
            <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-6">
                <div>
                    <h1 className="font-heading text-2xl font-bold text-foreground mb-1">{t('Form Responses')}</h1>
                    <p className="text-sm text-muted-foreground">
                        {t('View and export the responses to each of this event\'s forms.')}
                    </p>
                </div>

                <div className="bg-white rounded-2xl shadow-sm border border-border overflow-hidden">
                    {forms.length === 0 ? (
                        <p className="p-6 text-sm text-muted-foreground">{t('This event has no forms yet.')}</p>
                    ) : (
                        <div className="divide-y divide-border">
                            {forms.map(function(form) {
                                return (
                                    <div key={form.id} className="px-6 py-4 flex flex-wrap justify-between items-center gap-3">
                                        <div className="min-w-0 space-y-1">
                                            <div className="flex flex-wrap items-center gap-2">
                                                <strong className="text-sm font-semibold text-foreground">{form.name || t('Untitled Form')}</strong>
                                                {!form.is_active && (
                                                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-warning/10 text-warning-text border border-warning-border/50">
                                                        {t('Inactive')}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="text-xs text-muted-foreground">
                                                {this.formTypeLabel(form)}
                                                {' · '}
                                                {t('{{submitted}} submitted of {{total}} responses', {
                                                    submitted: form.submitted_count,
                                                    total: form.response_count
                                                })}
                                            </div>
                                        </div>
                                        <Link
                                            to={"/" + eventKey + "/form-responses/" + form.id}
                                            className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold border border-primary text-primary hover:bg-primary/10 transition-colors"
                                        >
                                            {t('View Responses')}
                                        </Link>
                                    </div>
                                );
                            }.bind(this))}
                        </div>
                    )}
                </div>
            </div>
        );
    }
}

export default withTranslation()(FormResponsesPage);
