import React, { Component } from "react";
import { withTranslation } from "react-i18next";
import { formConfigService } from "../../services/formConfig/formConfig.service";
import FormTypeCard from "./components/FormTypeCard";
import GenericFormsList from "./components/GenericFormsList";

class FormConfigPage extends Component {
    constructor(props) {
        super(props);
        this.state = {
            config: null,
            isLoading: true,
            error: null,
            creatingType: null,
            createError: null
        };
    }

    componentDidMount() {
        this.loadConfig();
    }

    loadConfig = () => {
        var event = this.props.event;
        if (!event) {
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

        return (
            <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-6">
                <div>
                    <h1 className="font-heading text-2xl font-bold text-foreground mb-1">{t('Form Configuration')}</h1>
                    <p className="text-sm text-muted-foreground">
                        {t('Manage which form system is used for each form type for this event.')}
                    </p>
                </div>

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
                    />
                    <FormTypeCard
                        title={t('Review Form')}
                        formTypeData={config && config.review}
                        eventKey={eventKey}
                        onCreateNew={function() { this.handleCreateTypedForm('review', 1); }.bind(this)}
                        isCreating={creatingType === 'review'}
                    />
                    <FormTypeCard
                        title={t('Registration Form')}
                        formTypeData={config && config.registration}
                        eventKey={eventKey}
                        onCreateNew={function() { this.handleCreateTypedForm('registration'); }.bind(this)}
                        isCreating={creatingType === 'registration'}
                    />
                </div>

                {config && config.review && config.review.system === 'new' && (
                    <div className="bg-white rounded-2xl shadow-sm border border-border p-6 space-y-4">
                        <div className="border-b border-border/50 pb-4">
                            <h2 className="text-lg font-semibold text-foreground/90">{t('Review Stages')}</h2>
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
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">{stage.stage}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground font-medium">{stage.form_name || t('Untitled')}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">{stage.num_reviews_required}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">{stage.completed_count} / {stage.total_count}</td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                                                    <a
                                                        href={"/" + eventKey + "/forms/" + stage.form_id + "/edit"}
                                                        className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold border border-primary text-primary hover:bg-primary/10 transition-colors"
                                                    >
                                                        {t('Edit')}
                                                    </a>
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
            </div>
        );
    }
}

export default withTranslation()(FormConfigPage);
