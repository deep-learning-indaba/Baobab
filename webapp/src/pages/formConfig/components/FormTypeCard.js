import React, { Component } from "react";
import { Link } from "react-router-dom";
import { withTranslation } from "react-i18next";

class FormTypeCard extends Component {
    render() {
        var t = this.props.t;
        var formTypeData = this.props.formTypeData;
        var title = this.props.title;
        var eventKey = this.props.eventKey;
        var onCreateNew = this.props.onCreateNew;
        var isCreating = this.props.isCreating;

        if (!formTypeData) {
            return (
                <div className="card mb-3">
                    <div className="card-body">
                        <h5 className="card-title">{title}</h5>
                        <p className="text-muted">{t('Not configured')}</p>
                    </div>
                </div>
            );
        }

        var isNew = formTypeData.system === 'new';
        var isOld = formTypeData.system === 'old';

        return (
            <div className={"card mb-3 " + (isNew ? "border-success" : "border-secondary")}>
                <div className="card-body">
                    <div className="d-flex justify-content-between align-items-start">
                        <div>
                            <h5 className="card-title">{title}</h5>
                            {isNew && (
                                <span className="badge badge-success mb-2">
                                    {t('New System')}
                                </span>
                            )}
                            {isOld && (
                                <span className="badge badge-secondary mb-2">
                                    {t('Legacy System')}
                                </span>
                            )}
                        </div>
                        <div>
                            {isNew && formTypeData.form_id && (
                                <Link
                                    to={"/" + eventKey + "/forms/" + formTypeData.form_id + "/edit"}
                                    className="btn btn-sm btn-outline-primary mr-2"
                                >
                                    {t('Edit Form')}
                                </Link>
                            )}
                            {isOld && onCreateNew && (
                                <button
                                    className="btn btn-sm btn-outline-success"
                                    onClick={onCreateNew}
                                    disabled={isCreating}
                                >
                                    {isCreating ? t('Creating...') : t('Migrate to New System')}
                                </button>
                            )}
                        </div>
                    </div>

                    {isNew && formTypeData.form_name && (
                        <p className="card-text">
                            <strong>{t('Form')}:</strong> {formTypeData.form_name}
                        </p>
                    )}

                    {isNew && (
                        <div className="row text-center mt-2">
                            {formTypeData.response_count !== undefined && (
                                <div className="col-4">
                                    <div className="h4 mb-0">{formTypeData.response_count}</div>
                                    <small className="text-muted">{t('Responses')}</small>
                                </div>
                            )}
                            {formTypeData.is_open !== undefined && (
                                <div className="col-4">
                                    <div className={"h5 mb-0 " + (formTypeData.is_open ? "text-success" : "text-danger")}>
                                        {formTypeData.is_open ? t('Open') : t('Closed')}
                                    </div>
                                    <small className="text-muted">{t('Status')}</small>
                                </div>
                            )}
                        </div>
                    )}

                    {isOld && formTypeData.legacy_form_id && (
                        <p className="card-text text-muted small">
                            {t('Legacy form ID')}: {formTypeData.legacy_form_id}
                        </p>
                    )}
                    {isOld && !formTypeData.legacy_form_id && (
                        <p className="card-text text-muted small">
                            {t('No form configured yet.')}
                        </p>
                    )}
                </div>
            </div>
        );
    }
}

export default withTranslation()(FormTypeCard);
