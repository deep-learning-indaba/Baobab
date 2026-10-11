import React, { Component } from "react";
import { withTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { formConfigService } from "../../services/formConfig/formConfig.service";
import FormTypeCard from "./components/FormTypeCard";
import GenericFormsList from "./components/GenericFormsList";
import SurveyFormConfig from "./components/SurveyFormConfig";
import { ConfirmModal } from "../../components/Modal";

class FormConfigPage extends Component {
    constructor(props) {
        super(props);
        this.state = {
            config: null,
            isLoading: true,
            error: null,
            creatingType: null,
            createError: null,
            confirmSwitchVisible: false,
            switching: false
        };
    }

    componentDidMount() {
        this.loadConfig();
    }

    loadConfig = () => {
        var event = this.props.event;
        if (!event) {
            // Don't sit on a spinner forever when the event prop is not ready.
            this.setState({ isLoading: false, error: this.props.t('Event information not available') });
            return;
        }
        this.setState({ isLoading: true, error: null });
        formConfigService.getFormConfig(event.id).then(function(result) {
            if (result.error) {
                this.setState({ error: result.error, isLoading: false });
            } else {
                this.setState({ config: result.config, isLoading: false });
            }
        }.bind(this));
    }

    handleCreateTypedForm = (formType, stage) => {
        var event = this.props.event;
        this.setState({ creatingType: formType, createError: null });
        formConfigService.createTypedForm(event.id, formType, stage).then(function(result) {
            if (result.error) {
                this.setState({ creatingType: null, createError: result.error });
            } else {
                this.setState({ creatingType: null });
                this.loadConfig();
            }
        }.bind(this));
    }

    handleSwitchSystem = () => {
        var event = this.props.event;
        var usesNewForms = !this.state.config.uses_new_forms;
        this.setState({ confirmSwitchVisible: false, switching: true, createError: null });
        formConfigService.setUsesNewForms(event.id, usesNewForms).then(function(result) {
            this.setState({ switching: false });
            if (result.error) {
                this.setState({ createError: result.error });
                return;
            }
            // The event (form ids, navigation) is loaded once by EventHome, so
            // reload to pick up the new system everywhere.
            window.location.reload();
        }.bind(this));
    }

    renderSystemSwitch() {
        var t = this.props.t;
        var usesNewForms = this.state.config.uses_new_forms;
        return (
            <div className="bg-white rounded-2xl shadow-sm border border-border p-6 flex flex-col md:flex-row md:items-center gap-4">
                <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                        <h2 className="text-base font-bold text-foreground">{t('Form system')}</h2>
                        <span className={"inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border " + (usesNewForms ? "bg-green-50 text-green-700 border-green-200" : "bg-amber-50 text-amber-700 border-amber-200")}>
                            {usesNewForms ? t('New System') : t('Legacy System')}
                        </span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                        {usesNewForms
                            ? t('Applications, reviews and registrations for this event use the new form system.')
                            : t('Applications, reviews and registrations for this event use the legacy forms.')}
                    </p>
                </div>
                <button
                    type="button"
                    className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-semibold border border-border text-foreground hover:bg-slate-50 transition-colors disabled:opacity-50"
                    onClick={function() { this.setState({ confirmSwitchVisible: true }); }.bind(this)}
                    disabled={this.state.switching}
                >
                    {usesNewForms ? t('Switch to legacy forms') : t('Switch to new forms')}
                </button>
                <ConfirmModal
                    visible={this.state.confirmSwitchVisible}
                    onOK={this.handleSwitchSystem}
                    onCancel={function() { this.setState({ confirmSwitchVisible: false }); }.bind(this)}
                    okText={t('Switch')}
                    cancelText={t('Cancel')}
                >
                    <p className="font-semibold mb-2">
                        {usesNewForms ? t('Switch this event to legacy forms?') : t('Switch this event to new forms?')}
                    </p>
                    <p>{t('Applicants, reviewers and organisers will immediately start using the other system. Responses already collected in this system are kept, but are not visible while the event uses the other one.')}</p>
                </ConfirmModal>
            </div>
        );
    }

    render() {
        var t = this.props.t;
        var config = this.state.config;
        var isLoading = this.state.isLoading;
        var error = this.state.error;
        var creatingType = this.state.creatingType;
        var createError = this.state.createError;
        var eventKey = this.props.eventKey;

        if (isLoading) {
            return (
                <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            );
        }

        if (error) {
            return (
                <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
                    {error}
                </div>
            );
        }

        var reviewStages = (config && config.review && config.review.stages) || [];
        var nextReviewStage = reviewStages.reduce(function(max, s) { return Math.max(max, s.stage || 0); }, 0) + 1;

        return (
            <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-6">
                <div>
                    <h1 className="font-heading text-2xl font-bold text-foreground mb-1">{t('Form Configuration')}</h1>
                    <p className="text-sm text-muted-foreground">
                        {t('Manage which form system is used for each form type for this event.')}
                    </p>
                </div>

                {config && this.renderSystemSwitch()}

                {createError && (
                    <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm flex justify-between items-center w-full" role="alert">
                        <span>{createError}</span>
                        <button
                            type="button"
                            className="text-error hover:text-error/80 transition-colors text-lg font-bold"
                            onClick={function() { this.setState({ createError: null }); }.bind(this)}
                            aria-label={t('Close')}
                        >
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <FormTypeCard
                        title={t('Application Form')}
                        formTypeData={config && config.application}
                        eventKey={eventKey}
                        onCreateNew={function() { this.handleCreateTypedForm('application'); }.bind(this)}
                        isCreating={creatingType === 'application'}
                        legacyEditUrl={'/' + eventKey + '/applicationform'}
                    />
                    <FormTypeCard
                        title={t('Review Form')}
                        formTypeData={config && config.review}
                        eventKey={eventKey}
                        onCreateNew={function() { this.handleCreateTypedForm('review', 1); }.bind(this)}
                        isCreating={creatingType === 'review'}
                        legacyEditUrl={'/' + eventKey + '/reviewForm'}
                    />
                    <FormTypeCard
                        title={t('Registration Form')}
                        formTypeData={config && config.registration}
                        eventKey={eventKey}
                        onCreateNew={function() { this.handleCreateTypedForm('registration'); }.bind(this)}
                        isCreating={creatingType === 'registration'}
                        legacyEditUrl={null}
                    />
                </div>


                {config && config.review && config.review.system === 'new' && reviewStages.length > 0 && (
                    <div className="bg-white rounded-2xl shadow-sm border border-border p-6 space-y-4">
                        <div className="border-b border-border/50 pb-4 flex items-center justify-between gap-3">
                            <h2 className="text-lg font-semibold text-foreground/90">{t('Review Stages')}</h2>
                            <button
                                type="button"
                                className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold border border-green-500 text-green-600 hover:bg-green-50 transition-colors disabled:opacity-50"
                                onClick={function() { this.handleCreateTypedForm('review', nextReviewStage); }.bind(this)}
                                disabled={creatingType === 'review'}
                            >
                                {creatingType === 'review' ? t('Creating...') : t('Add Review Stage')}
                            </button>
                        </div>
                        <div className="overflow-x-auto rounded-xl border border-border">
                            <table className="min-w-full divide-y divide-border">
                                <thead className="bg-slate-50">
                                    <tr>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">{t('Stage')}</th>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">{t('Form Name')}</th>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">{t('Required Reviews')}</th>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">{t('Completed')}</th>
                                        <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">{t('Actions')}</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-border">
                                    {config.review.stages.map(function(stage) {
                                        return (
                                            <tr key={stage.stage} className="hover:bg-slate-50/50 transition-colors">
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                                                    {stage.stage}
                                                    {stage.is_active && (
                                                        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-green-50 text-green-700 border border-green-200/50">{t('Active')}</span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground font-medium">{stage.form_name || t('Untitled')}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">{stage.num_reviews_required}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">{stage.completed_count} / {stage.total_count}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                                                    <Link
                                                        to={"/" + eventKey + "/forms/" + stage.form_id + "/edit"}
                                                        className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold border border-primary text-primary hover:bg-primary/10 transition-colors"
                                                    >
                                                        {t('Edit')}
                                                    </Link>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                <div>
                    <GenericFormsList
                        forms={config && config.generic_forms}
                        eventKey={eventKey}
                    />
                </div>

                <SurveyFormConfig
                    eventId={this.props.event && this.props.event.id}
                    eventTimezone={this.props.event && this.props.event.timezone}
                    surveyFormId={config && config.survey && config.survey.form_id}
                    surveyOpen={config && config.survey && config.survey.survey_open}
                    onSaved={this.loadConfig}
                />
            </div>
        );
    }
}

export default withTranslation()(FormConfigPage);
