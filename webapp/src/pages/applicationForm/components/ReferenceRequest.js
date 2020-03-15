import React from "react";
import FormGroup from "../../../components/form/FormGroup";
import FormToolTip from "../../../components/form/FormToolTip";
import { referenceService } from "../../../services/references/reference.service";
import _ from "lodash";
import ReactToolTip from "react-tooltip";

// TODO: Add validation to enforce that references must be requested first.
// TODO: Add validation that fields must be filled in before references can be requested.
// TODO: Set value in application form after requesting references and trigger saving response (so that reference requests and application form state is set)

class ReferenceRequestRow extends React.Component {
    constructor(props) {
        super(props);
        this.state = {

        }
    }

    onChange = e => {
        if (this.props.onChange) {
            this.props.onChange(this.props.referenceRequest.id, e.target.name, e.target.value);
        }
    }

    deleteReference = e => {
        if (this.props.onDelete) {
            this.props.onDelete(this.props.referenceRequest.id);
        }
    }

    render() {
        return (
            <div>
                <div className="row no-gutters reference-row">
                    <div className="col-sm">
                        <input
                            id={this.props.Id + "_title"}
                            name="title"
                            className="form-control"
                            type="text"
                            placeholder="Title"
                            value={this.props.referenceRequest.title}
                            onChange={this.onChange}
                            required={!this.props.referenceRequest.emailSent}
                            readOnly={this.props.referenceRequest.emailSent}
                        />
                    </div>
                    <div className="col-sm">
                        <input
                            id={this.props.Id + "_firstname"}
                            name="firstname"
                            className="form-control"
                            type="text"
                            placeholder="Firstname"
                            value={this.props.referenceRequest.firstname}
                            onChange={this.onChange}
                            required={!this.props.referenceRequest.emailSent}
                            readOnly={this.props.referenceRequest.emailSent}
                        />
                    </div>
                    <div className="col-sm">
                        <input
                            id={this.props.Id + "_lastname"}
                            name="lastname"
                            className="form-control"
                            type="text"
                            placeholder="Lastname"
                            value={this.props.referenceRequest.lastname}
                            onChange={this.onChange}
                            required={!this.props.referenceRequest.emailSent}
                            readOnly={this.props.referenceRequest.emailSent}
                        />
                    </div>
                    <div className="col-sm">
                        <input
                            id={this.props.Id + "_email"}
                            name="email"
                            className="form-control"
                            type="text"
                            placeholder="Email"
                            value={this.props.referenceRequest.email}
                            onChange={this.onChange}
                            required={!this.props.referenceRequest.emailSent}
                            readOnly={this.props.referenceRequest.emailSent}
                        />
                    </div>
                    <div className="col-sm">
                        <input
                            id={this.props.Id + "_relation"}
                            name="relation"
                            className="form-control"
                            type="text"
                            placeholder="Relation"
                            value={this.props.referenceRequest.relation}
                            onChange={this.onChange}
                            required={!this.props.referenceRequest.emailSent}
                            readOnly={this.props.referenceRequest.emailSent}
                        />
                    </div>
                    <div className="col-auto reference-status">
                        {this.props.referenceRequest.loading &&
                            <div class="spinner-border" role="status">
                                <span class="sr-only">Loading...</span>
                            </div>
                        }

                        {this.props.referenceRequest.emailSent &&
                            (this.props.referenceRequest.referenceSubmitted
                                ? <div><i className="fas fa-check-double text-success" data-top="Reference has been received."></i><ReactToolTip type="info" place="right" effect="solid" /></div>
                                : <div><i className="fas fa-check" data-tip="Email has been sent"></i><ReactToolTip type="info" place="right" effect="solid" /></div>)
                        }

                        {(!this.props.emailSent) && this.props.minReferences && this.props.referenceNumber > this.props.minReferences
                            && <button className="link-style" onClick={this.deleteReference}><i className="fas fa-trash text-danger"></i></button>
                        }

                    </div>
                </div>
                {this.props.referenceRequest.error && <div class="row no-gutters">
                    <span className="text-danger">ERROR: {JSON.stringify(this.props.referenceRequest.error)}</span>
                </div>}
            </div>
        )
    }
}

class FormReferenceRequest extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            referenceRequests: [],
            minId: 0,
            error: null
        };
    }

    getRequestStatus = () => {
        if (this.props.responseId) {
            referenceService.getReferenceRequests(this.props.responseId).then(response => {
                // Map email_sent and reference_submitted to state.referenceRequests
                if (response.requests) {
                    this.setState(prevState => {
                        let updatedReferenceRequests = prevState.referenceRequests.map(r => {
                            let requestStatus = _.find(response.requests, s => s.id === r.id);
                            return {
                                ...r,
                                emailSent: requestStatus ? requestStatus.email_sent : false,
                                referenceSubmitted: requestStatus ? requestStatus.reference_submitted : false,
                                loading: false
                            }
                        })
                        return {
                            referenceRequests: updatedReferenceRequests
                        };
                    });
                }
                else if (response.error) {
                    this.setState({
                        error: response.error
                    });
                }
            });
        }
    }

    componentDidMount() {
        this.setState({
            loading: true
        });

        if (this.props.responseId) {
            referenceService.getReferenceRequests(this.props.responseId).then(response => {
                // Map email_sent and reference_submitted to state.referenceRequests
                if (response.requests) {
                    let initialReferenceRequests = response.requests.map(r => ({
                        id: r.id,
                        key: r.id,
                        title: r.title,
                        firstname: r.firstname,
                        lastname: r.lastname,
                        email: r.email,
                        relation: r.relation,
                        loading: false,
                        error: null,
                        emailSent: !!r.email_sent,
                        referenceSubmitted: r.reference_submitted
                    }));

                    let minId = -1;

                    for (let i = initialReferenceRequests.length; i < this.props.options.min_num_referrals; i++) {
                        initialReferenceRequests.push({
                            id: minId - 1,
                            key: minId - 1,
                            title: '',
                            firstname: '',
                            lastname: '',
                            email: '',
                            relation: '',
                            loading: false,
                            error: null
                        });
                        minId--;
                    }

                    this.setState({
                        referenceRequests: initialReferenceRequests,
                        minId: minId,
                        loading: false
                    });
                }
                else {
                    this.setState({
                        loading: false,
                        error: response.error
                    });
                }
            });
        }
    }

    shouldDisplayError = () => {
        return this.props.showError && this.props.errorText !== "";
    };

    componentWillReceiveProps(nextProps) {
        if (nextProps.showFocus) {
            this.nameInput.focus();
        }
    }

    onChange = (id, name, value) => {
        this.setState(prevState => {
            var updatedReferenceRequest = _.find(prevState.referenceRequests, r => r.id === id);
            updatedReferenceRequest[name] = value;
            return {
                referenceRequests: prevState.referenceRequests.map(r => {
                    return r.id === id ? updatedReferenceRequest : r
                })
            };
        });
    }

    onDelete = (id) => {
        this.setState(prevState => {
            return {
                referenceRequests: prevState.referenceRequests.filter(r => r.id !== id)
            };
        })
    }

    addRow = e => {
        this.setState(prevState => {
            return {
                referenceRequests: [...prevState.referenceRequests, {
                    id: prevState.minId - 1,
                    key: prevState.minId - 1,
                    title: '',
                    firstname: '',
                    lastname: '',
                    email: '',
                    relation: '',
                    loading: false,
                    error: null
                }],
                minId: prevState.minId - 1
            };
        });
    }

    submit = e => {
        this.setState(prevState => ({
            referenceRequests: prevState.referenceRequests.map(r => ({
                ...r,
                loading: r.id < 0
            }))
        }));

        this.state.referenceRequests
            .filter(r => r.id < 0 && !r.emailSent)
            .forEach(rr => {
                referenceService.requestReference(this.props.responseId, rr.title, rr.firstname, rr.lastname, rr.email, rr.relation)
                    .then(response => {
                        this.setState(prevState => ({
                            referenceRequests: prevState.referenceRequests.map(r => {
                                if (r.id === rr.id) {
                                    if (response.referenceRequest) {
                                        return {
                                            id: response.referenceRequest.id,
                                            key: r.key,
                                            title: response.referenceRequest.title,
                                            firstname: response.referenceRequest.firstname,
                                            lastname: response.referenceRequest.lastname,
                                            email: response.referenceRequest.email,
                                            relation: response.referenceRequest.relation,
                                            loading: false,
                                            error: null,
                                            emailSent: !!response.referenceRequest.email_sent,
                                            referenceSubmitted: response.referenceRequest.reference_submitted
                                        };
                                    }
                                    else {
                                        return {
                                            ...rr,
                                            error: response.error
                                        };
                                    }
                                }
                                else {
                                    return r;
                                }
                            })
                        }))
                    });
            });
    }

    render() {
        const { referenceRequests } = this.state;
        return (
            <div>
                <FormGroup
                    id={this.props.Id + "-group"}
                    errorText={this.props.errorText}
                    tabIndex={this.props.tabIndex}
                    autoFocus={this.props.autoFocus}
                >
                    <div className="rowC">
                        <label htmlFor={this.props.id}>{this.props.label}</label>
                        {this.props.description ? (
                            <FormToolTip description={this.props.description} />
                        ) : (
                                <div />
                            )}
                    </div>
                    <div>{referenceRequests.map((r, i) =>
                        <ReferenceRequestRow
                            key={'rr_' + r.key}
                            referenceRequest={r}
                            onChange={this.onChange}
                            onDelete={this.onDelete}
                            minReferences={this.props.options.min_num_referrals}
                            referenceNumber={i + 1}
                        />)
                    }</div>
                    {this.props.options && this.props.options.max_num_referrals && this.props.options.max_num_referrals > this.state.referenceRequests.length &&
                        <button className="link-style text-success float-right add-button" onClick={this.addRow}><i class="fas fa-plus-circle"></i><span> Add</span></button>
                    }
                    <button className="btn btn-primary btn-sm" onClick={this.submit}>Request References</button>
                    {this.state.error && <div className="text-danger">ERROR: {JSON.stringify(this.state.error)}</div>}
                    {this.state.loading && <div class="spinner-border" role="status">
                                <span class="sr-only">Loading...</span>
                            </div>}
                </FormGroup>
            </div>
        )
    }
}

export default FormReferenceRequest;