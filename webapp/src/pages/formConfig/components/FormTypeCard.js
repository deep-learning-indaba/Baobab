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
        var legacyEditUrl = this.props.legacyEditUrl;

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
        var hasLegacyForm = isOld && formTypeData.legacy_form_id != null;
        var isNoForm = isOld && !formTypeData.legacy_form_id;

        return (
            <div className={"bg-white rounded-2xl shadow-sm border p-6 mb-3 transition-colors " + (isNew ? "border-green-200 bg-green-50/5" : hasLegacyForm ? "border-amber-200 bg-amber-50/5" : "border-slate-200 bg-slate-50/5")}>
                <div className="space-y-4">
                    <div className="flex justify-between items-start gap-3">
                        <div className="space-y-1 min-w-0">
                            <h5 className="text-base font-bold text-foreground">{title}</h5>
                            {isNew && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-50 text-green-700 border border-green-200/50">
                                    {t('New System')}
                                </span>
                            )}
                            {hasLegacyForm && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                                    {t('Legacy System')}
                                </span>
                            )}
                            {isNoForm && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                                    {t('Not Created')}
                                </span>
                            )}
                        </div>

                        <div className="flex flex-col gap-1.5 items-end shrink-0">
                            {/* New system: link to form editor */}
                            {isNew && formTypeData.form_id && (
                                <Link
                                    to={"/" + eventKey + "/forms/" + formTypeData.form_id + "/edit"}
                                    className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold border border-primary text-primary hover:bg-primary/10 transition-colors"
                                >
                                    {t('Edit Form')}
                                </Link>
                            )}

                            {/* Legacy system with existing form: link to legacy editor */}
                            {hasLegacyForm && legacyEditUrl && (
                                <a
                                    href={legacyEditUrl}
                                    className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold border border-amber-500 text-amber-700 hover:bg-amber-50 transition-colors"
                                >
                                    {t('Edit Legacy Form')}
                                </a>
                            )}

                            {/* No form yet: offer to create new-system form */}
                            {isNoForm && onCreateNew && (
                                <button
                                    className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold border border-green-500 text-green-600 hover:bg-green-50 transition-colors"
                                    onClick={onCreateNew}
                                    disabled={isCreating}
                                >
                                    {isCreating ? t('Creating...') : t('Create New Form')}
                                </button>
                            )}

                            {/* No form yet and legacy editor available: revert option */}
                            {isNoForm && legacyEditUrl && (
                                <a
                                    href={legacyEditUrl}
                                    className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-300 text-slate-500 hover:bg-slate-50 transition-colors"
                                >
                                    {t('Revert to Legacy')}
                                </a>
                            )}
                        </div>
                    </div>

                    {isNew && formTypeData.form_name && (
                        <p className="text-sm text-foreground">
                            <strong className="font-semibold text-foreground/90">{t('Form')}:</strong> {formTypeData.form_name}
                        </p>
                    )}

                    {isNew && (formTypeData.response_count !== undefined || formTypeData.is_open !== undefined) && (
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

                    {hasLegacyForm && (
                        <p className="text-xs text-muted-foreground">
                            {t('Legacy form ID')}: {formTypeData.legacy_form_id}
                        </p>
                    )}

                    {isNoForm && !legacyEditUrl && (
                        <p className="text-xs text-muted-foreground">
                            {t('No form configured yet.')}
                        </p>
                    )}

                    {hasLegacyForm && !legacyEditUrl && (
                        <p className="text-xs text-muted-foreground italic">
                            {t('No editor available for this legacy form.')}
                        </p>
                    )}
                </div>
            </div>
        );
    }
}

export default withTranslation()(FormTypeCard);
