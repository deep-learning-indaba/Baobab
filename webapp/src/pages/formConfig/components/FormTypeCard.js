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
                <div className="bg-white rounded-2xl shadow-sm border border-border p-6 mb-3">
                    <h5 className="text-base font-bold text-foreground mb-2">{title}</h5>
                    <p className="text-sm text-muted-foreground">{t('Not configured')}</p>
                </div>
            );
        }

        var isNew = formTypeData.system === 'new';
        var isOld = formTypeData.system === 'old';

        return (
            <div className={"bg-white rounded-2xl shadow-sm border p-6 mb-3 transition-colors " + (isNew ? "border-green-200 bg-green-50/5" : "border-slate-200 bg-slate-50/5")}>
                <div className="space-y-4">
                    <div className="flex justify-between items-start gap-4">
                        <div className="space-y-1">
                            <h5 className="text-base font-bold text-foreground">{title}</h5>
                            {isNew && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-50 text-green-700 border border-green-200/50">
                                    {t('New System')}
                                </span>
                            )}
                            {isOld && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                                    {t('Legacy System')}
                                </span>
                            )}
                        </div>
                        <div>
                            {isNew && formTypeData.form_id && (
                                <Link
                                    to={"/" + eventKey + "/forms/" + formTypeData.form_id + "/edit"}
                                    className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold border border-primary text-primary hover:bg-primary/10 transition-colors"
                                >
                                    {t('Edit Form')}
                                </Link>
                            )}
                            {isOld && onCreateNew && (
                                <button
                                    className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold border border-green-500 text-green-600 hover:bg-green-50 transition-colors"
                                    onClick={onCreateNew}
                                    disabled={isCreating}
                                >
                                    {isCreating ? t('Creating...') : t('Migrate to New System')}
                                </button>
                            )}
                        </div>
                    </div>

                    {isNew && formTypeData.form_name && (
                        <p className="text-sm text-foreground">
                            <strong className="font-semibold text-foreground/90">{t('Form')}:</strong> {formTypeData.form_name}
                        </p>
                    )}

                    {isNew && (
                        <div className="grid grid-cols-2 gap-4 text-center pt-2 border-t border-border/50">
                            {formTypeData.response_count !== undefined && (
                                <div>
                                    <div className="text-xl font-bold text-foreground">{formTypeData.response_count}</div>
                                    <small className="text-xs text-muted-foreground">{t('Responses')}</small>
                                </div>
                            )}
                            {formTypeData.is_open !== undefined && (
                                <div>
                                    <div className={"text-base font-bold " + (formTypeData.is_open ? "text-green-600" : "text-error")}>
                                        {formTypeData.is_open ? t('Open') : t('Closed')}
                                    </div>
                                    <small className="text-xs text-muted-foreground">{t('Status')}</small>
                                </div>
                            )}
                        </div>
                    )}

                    {isOld && formTypeData.legacy_form_id && (
                        <p className="text-xs text-muted-foreground">
                            {t('Legacy form ID')}: {formTypeData.legacy_form_id}
                        </p>
                    )}
                    {isOld && !formTypeData.legacy_form_id && (
                        <p className="text-xs text-muted-foreground">
                            {t('No form configured yet.')}
                        </p>
                    )}
                </div>
            </div>
        );
    }
}

export default withTranslation()(FormTypeCard);
