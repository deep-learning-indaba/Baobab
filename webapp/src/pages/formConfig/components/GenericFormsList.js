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
            <div className="card mb-3">
                <div
                    className="card-header d-flex justify-content-between align-items-center"
                    style={{ cursor: "pointer" }}
                    onClick={this.toggleCollapse}
                >
                    <h5 className="mb-0">
                        {t('Other Forms')}
                        <span className="badge badge-light ml-2">{forms.length}</span>
                    </h5>
                    <span className={"fas " + (collapsed ? "fa-chevron-down" : "fa-chevron-up")} />
                </div>
                {!collapsed && (
                    <div className="card-body">
                        {forms.length === 0 ? (
                            <p className="text-muted mb-0">{t('No generic forms created yet.')}</p>
                        ) : (
                            <div className="list-group list-group-flush">
                                {forms.map(function(form) {
                                    return (
                                        <div
                                            key={form.id}
                                            className="list-group-item d-flex justify-content-between align-items-center px-0"
                                        >
                                            <div>
                                                <strong>{form.name || t('Untitled Form')}</strong>
                                                <span className="text-muted small ml-2">
                                                    ({form.response_count} {t('responses')})
                                                </span>
                                                {!form.is_active && (
                                                    <span className="badge badge-warning ml-2">
                                                        {t('Inactive')}
                                                    </span>
                                                )}
                                            </div>
                                            <div>
                                                <Link
                                                    to={"/" + eventKey + "/forms/" + form.id + "/edit"}
                                                    className="btn btn-sm btn-outline-primary mr-2"
                                                >
                                                    {t('Edit')}
                                                </Link>
                                                <Link
                                                    to={"/" + eventKey + "/form-responses/" + form.id}
                                                    className="btn btn-sm btn-outline-secondary"
                                                >
                                                    {t('Responses')}
                                                </Link>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                        <div className="mt-3">
                            <Link
                                to={"/" + eventKey + "/forms/new"}
                                className="btn btn-sm btn-outline-primary"
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
