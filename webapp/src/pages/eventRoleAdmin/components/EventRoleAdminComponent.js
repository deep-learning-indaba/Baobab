import React, { Component } from 'react';
import { eventService } from "../../../services/events";
import { withRouter } from 'react-router-dom';
import { withTranslation } from 'react-i18next';

class EventRoleAdminComponent extends Component {

    constructor(props) {
        super(props);
        this.state = {
            eventRoles: []
        };
    }

    componentDidMount() {
        eventService.getEventRoles(this.props.event.id).then(result => {
            this.setState({
                eventRoles: result.eventRoles
            });
        });
    }

    onDeleteRole = (roleId) => {
        eventService.deleteEventRole(this.props.event.id, roleId).then(result => {
            this.setState({
                eventRoles: result.eventRoles
            });
        });
    }

    onAddRole = (e) => {
        e.preventDefault();
        const email = e.target.email.value;
        const role = e.target.role.value;
        eventService.addEventRole(this.props.event.id, email, role).then(result => {
            this.setState({
                eventRoles: result.eventRoles
            });
        });
    }
    
    render() {
        return (
        <div className="container mt-4">
            <h1 className="mb-4">Event Role Admin</h1>
            <div className="card mb-4">
                <div className="card-header">
                    <h2 className="mb-0">Event Role List</h2>
                </div>
                <div className="card-body">
                    <div className="table-responsive">
                        <table className="table table-striped table-hover">
                            <thead className="thead-dark">
                            <tr>
                                <th>Role</th>
                                <th>User</th>
                                <th>Actions</th>
                            </tr>
                            </thead>
                            <tbody>
                            {this.state.eventRoles.map(role => (
                                <tr key={role.id}>
                                    <td>{role.role}</td>
                                    <td>{role.user.full_name}</td>
                                    <td>
                                        <button 
                                            className="btn btn-danger btn-sm"
                                            onClick={() => this.onDeleteRole(role.id)}>
                                            <i className="fa fa-trash"></i>
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div className="card">
                <div className="card-header">
                    <h2 className="mb-0">Add Event Role</h2>
                </div>
                <div className="card-body">
                    <form onSubmit={this.onAddRole}>
                        <div className="form-group mb-3">
                            <label htmlFor="email">{this.props.t("User Email")}</label>
                            <input 
                                className="form-control"
                                id="email"
                                type="email"
                                name="email"
                                placeholder={this.props.t("User Email")}
                                required
                            />
                        </div>
                        <div className="form-group mb-3">
                            <label htmlFor="role">{this.props.t("Role")}</label>
                            <select className="form-control" id="role" name="role">
                                <option value="admin">{this.props.t("Event Admin")}</option>
                                <option value="reviewer">{this.props.t("Reviewer")}</option>
                                <option value="registration-admin">{this.props.t("Registration Admin")}</option>
                                <option value="registration-volunteer">{this.props.t("Registration Volunteer")}</option>
                                <option value="treasurer">{this.props.t("Event Treasurer")}</option>
                            </select>
                        </div>
                        <button type="submit" className="btn btn-primary">{this.props.t("Add Role")}</button>
                    </form>
                </div>
            </div>
        </div>
        );
    }
}

export default withRouter(withTranslation()(EventRoleAdminComponent));