import React, { Component } from "react";
import { Link } from "react-router-dom";
import { withTranslation } from "react-i18next";

class GenericFormsList extends Component {
    constructor(props) {
        super(props);
        this.state = {
            collapsed: true
        };
    }

    toggleCollapse = () => {
        this.setState(function(prev) {
            return { collapsed: !prev.collapsed };
        });
    }

    render() {
        var t = this.props.t;
        var forms = this.props.forms || [];
        var eventKey = this.props.eventKey;
        var collapsed = this.state.collapsed;

        return (
            <div className="bg-white rounded-2xl shadow-sm border border-border overflow-hidden mb-3">
                <div
                    className="px-6 py-4 flex justify-between items-center bg-slate-50 border-b border-border/50 cursor-pointer select-none"
                    onClick={this.toggleCollapse}
                >
                    <h5 className="text-base font-bold text-foreground flex items-center gap-2">
                        {t('Other Forms')}
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-white text-muted-foreground border border-border">{forms.length}</span>
                    </h5>
                    <span className={"fas text-muted-foreground " + (collapsed ? "fa-chevron-down" : "fa-chevron-up")} />
                </div>
                {!collapsed && (
                    <div className="p-6 space-y-4">
                        {forms.length === 0 ? (
                            <p className="text-sm text-muted-foreground">{t('No generic forms created yet.')}</p>
                        ) : (
                            <div className="divide-y divide-border">
                                {forms.map(function(form) {
                                    return (
                                        <div
                                            key={form.id}
                                            className="py-4 flex justify-between items-center first:pt-0 last:pb-0"
                                        >
                                            <div className="flex items-center gap-2">
                                                <strong className="text-sm font-semibold text-foreground">{form.name || t('Untitled Form')}</strong>
                                                <span className="text-xs text-muted-foreground">
                                                    ({form.response_count} {t('responses')})
                                                </span>
                                                {!form.is_active && (
                                                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-warning/10 text-warning-text border border-warning-border/50">
                                                        {t('Inactive')}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="flex items-center">
                                                <Link
                                                    to={"/" + eventKey + "/forms/" + form.id + "/edit"}
                                                    className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold border border-primary text-primary hover:bg-primary/10 transition-colors mr-2"
                                                >
                                                    {t('Edit')}
                                                </Link>
                                                <Link
                                                    to={"/" + eventKey + "/form-responses/" + form.id}
                                                    className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold border border-border text-muted-foreground hover:bg-slate-50 transition-colors"
                                                >
                                                    {t('Responses')}
                                                </Link>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                        <div className="pt-2">
                            <Link
                                to={"/" + eventKey + "/forms/new"}
                                className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold border border-primary text-primary hover:bg-primary/10 transition-colors"
                            >
                                + {t('Create New Form')}
                            </Link>
                        </div>
                    </div>
                )}
            </div>
        );
    }
}

export default withTranslation()(GenericFormsList);
