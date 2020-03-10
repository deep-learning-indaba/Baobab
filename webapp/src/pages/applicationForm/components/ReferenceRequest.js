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

    render() {
        return (
            <div className="form-inline">
                <input
                    id={this.props.Id + "_title"}
                    name="title"
                    className="form-control"
                    type="text"
                    placeholder="Title"
                    value={this.props.referenceRequest.title}
                    onChange={this.props.onChange}
                    required="true"
                />
                <input
                    id={this.props.Id + "_firstname"}
                    name="firstname"
                    className="form-control"
                    type="text"
                    placeholder="Firstname"
                    value={this.props.referenceRequest.firstname}
                    onChange={this.props.onChange}
                    required="true"
                />
                <input
                    id={this.props.Id + "_lastname"}
                    name="lastname"
                    className="form-control"
                    type="text"
                    placeholder="Lastname"
                    value={this.props.referenceRequest.lastname}
                    onChange={this.props.onChange}
                    required="true"
                />
                <input
                    id={this.props.Id + "_email"}
                    name="email"
                    className="form-control"
                    type="text"
                    placeholder="Email"
                    value={this.props.referenceRequest.email}
                    onChange={this.props.onChange}
                    required="true"
                />
                <input
                    id={this.props.Id + "_relation"}
                    name="relation"
                    className="form-control"
                    type="text"
                    placeholder="Relation"
                    value={this.props.referenceRequest.relation}
                    onChange={this.props.onChange}
                    required="true"
                />
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
        if (this.props.defaultValue) {
            this.setState({
                referenceRequests: this.props.defaultValue
            })
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
            var updatedReferenceRequest = prevState.referenceRequests.find(r => r.id === id);
            updatedReferenceRequest[name] = value;
            return {
                referenceRequests: prevState.referenceRequests.map(r => {
                    return r.id === id ? updatedReferenceRequest : r
                })
            };
        });
    }

    addRow = e => {
        this.setState(prevState => {
            return {
                referenceRequests: [...prevState, {
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
                    <div>{referenceRequests.map(r => <ReferenceRequestRow key={'rr_' + r.id} referenceRequest={r} />)}</div>
                    <button className="link-style text-success" onClick={this.addRow}><i class="fas fa-plus-circle"></i></button>
                </FormGroup>
            </div>
        )
    }



}

export default FormReferenceRequest;