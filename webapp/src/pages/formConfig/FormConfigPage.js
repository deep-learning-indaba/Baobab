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
                <div className="d-flex justify-content-center mt-5">
                    <div className="spinner-border" role="status">
                        <span className="sr-only">{t('Loading')}</span>
                    </div>
                </div>
            );
        }

        if (error) {
            return (
                <div className="alert alert-danger mt-3">
                    {error}
                </div>
            );
        }

        return (
            <div className="container-fluid mt-4">
                <h2>{t('Form Configuration')}</h2>
                <p className="text-muted">
                    {t('Manage which form system is used for each form type for this event.')}
                </p>

                {createError && (
                    <div className="alert alert-danger alert-dismissible fade show" role="alert">
                        {createError}
                        <button
                            type="button"
                            className="close"
                            onClick={function() { this.setState({ createError: null }); }.bind(this)}
                            aria-label={t('Close')}
                        >
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                )}

                <div className="row">
                    <div className="col-md-4">
                        <FormTypeCard
                            title={t('Application Form')}
                            formTypeData={config && config.application}
                            eventKey={eventKey}
                            onCreateNew={function() { this.handleCreateTypedForm('application'); }.bind(this)}
                            isCreating={creatingType === 'application'}
                        />
                    </div>
                    <div className="col-md-4">
                        <FormTypeCard
                            title={t('Review Form')}
                            formTypeData={config && config.review}
                            eventKey={eventKey}
                            onCreateNew={function() { this.handleCreateTypedForm('review', 1); }.bind(this)}
                            isCreating={creatingType === 'review'}
                        />
                    </div>
                    <div className="col-md-4">
                        <FormTypeCard
                            title={t('Registration Form')}
                            formTypeData={config && config.registration}
                            eventKey={eventKey}
                            onCreateNew={function() { this.handleCreateTypedForm('registration'); }.bind(this)}
                            isCreating={creatingType === 'registration'}
                        />
                    </div>
                </div>

                {config && config.review && config.review.system === 'new' && (
                    <div className="row">
                        <div className="col-12">
                            <div className="card mb-3">
                                <div className="card-header">
                                    <h5 className="mb-0">{t('Review Stages')}</h5>
                                </div>
                                <div className="card-body">
                                    <div className="table-responsive">
                                        <table className="table table-sm">
                                            <thead>
                                                <tr>
                                                    <th>{t('Stage')}</th>
                                                    <th>{t('Form Name')}</th>
                                                    <th>{t('Required Reviews')}</th>
                                                    <th>{t('Completed')}</th>
                                                    <th>{t('Actions')}</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {config.review.stages.map(function(stage) {
                                                    return (
                                                        <tr key={stage.stage}>
                                                            <td>{stage.stage}</td>
                                                            <td>{stage.form_name || t('Untitled')}</td>
                                                            <td>{stage.num_reviews_required}</td>
                                                            <td>{stage.completed_count} / {stage.total_count}</td>
                                                            <td>
                                                                <a
                                                                    href={"/" + eventKey + "/forms/" + stage.form_id + "/edit"}
                                                                    className="btn btn-sm btn-outline-primary"
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
                            </div>
                        </div>
                    </div>
                )}

                <div className="row">
                    <div className="col-12">
                        <GenericFormsList
                            forms={config && config.generic_forms}
                            eventKey={eventKey}
                        />
                    </div>
                </div>
            </div>
        );
    }
}

export default withTranslation()(FormConfigPage);
