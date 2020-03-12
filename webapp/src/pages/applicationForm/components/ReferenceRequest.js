import React from "react";
import FormGroup from "../../../components/form/FormGroup";
import FormToolTip from "../../../components/form/FormToolTip";

class ReferenceRequestRow extends React.Component {
    constructor(props) {
        super(props);
        this.state = {

        }
    }

    componentDidMount() {
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
                            required="true"
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
                            required="true"
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
                            required="true"
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
                            required="true"
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
                            required="true"
                        />
                    </div>
                    <div className="col-auto reference-delete">
                        {/* Todo: Remove button if request already sent (add a checkmark instead?) */}
                        {this.props.minReferences && this.props.referenceNumber > this.props.minReferences
                            && <button className="link-style" onClick={this.deleteReference}><i className="fas fa-trash text-danger"></i></button>
                        }

                    </div>
                </div>
            </div>
        )
    }
}

class FormReferenceRequest extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            referenceRequests: [],
            minId: 0
        };
    }

    componentDidMount() {
        var initialReferenceRequests = this.props.defaultValue || [];
        var minId = -1;
        if (this.props.options.min_num_referrals > initialReferenceRequests.length) {
            for(var i = initialReferenceRequests.length; i < this.props.options.min_num_referrals; i++) {
                initialReferenceRequests.push({
                    id: minId--,
                    title: null,
                    firstname: null,
                    lastname: null,
                    email: null,
                    relation: null
                });
            }
        }
        
        this.setState({
            referenceRequests: initialReferenceRequests,
            minId: minId
        });
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
            var updatedReferenceRequest = prevState.referenceRequests.find(r => r.id === id);
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
                    title: null,
                    firstname: null,
                    lastname: null,
                    email: null,
                    relation: null
                }],
                minId: prevState.minId - 1
            };
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
                            key={'rr_' + r.id}
                            referenceRequest={r}
                            onChange={this.onChange}
                            onDelete={this.onDelete}
                            minReferences={this.props.options.min_num_referrals}
                            referenceNumber={i+1}
                        />)
                    }</div>
                    {this.props.options && this.props.options.max_num_referrals && this.props.options.max_num_referrals > this.state.referenceRequests.length &&
                        <button className="link-style text-success float-right add-button" onClick={this.addRow}><i class="fas fa-plus-circle"></i><span> Add</span></button>
                    }
                </FormGroup>
            </div>
        )
    }



}

export default FormReferenceRequest;