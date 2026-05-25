import React, { Component } from 'react';
import { eventService } from "../../../services/events";
import { withRouter } from 'react-router-dom';
import { withTranslation } from 'react-i18next';

class EventRoleAdminComponent extends Component {

    constructor(props) {
        super(props);
        this.state = {
            eventRoles: [],
            isLoading: true,
            error: "",
            userNotFound: false,
            duplicateRole: false
        };
    }

    componentDidMount() {
        eventService.getEventRoles(this.props.event.id).then(result => {
            this.setState({
                eventRoles: result.eventRoles,
                isLoading: false,
                error: result.error
            });
        });
    }

    onDeleteRole = (roleId) => {
        eventService.deleteEventRole(this.props.event.id, roleId).then(result => {
            this.setState({
                eventRoles: this.state.eventRoles.filter(role => role.id !== roleId),
                error: result.error
            });
        });
    }

    onAddRole = (e) => {
        e.preventDefault();
        const form = e.target;
        const email = form.email.value;
        const role = form.role.value;

        eventService.addEventRole(this.props.event.id, email, role).then(result => {
            if (result.error) {
                this.setState({
                    userNotFound: result.error === "No user exists with that email",
                    duplicateRole: result.error === 'This user already has this role for this event.',
                    error: result.error
                });
            } else {
                this.setState({
                    eventRoles: result.eventRoles,
                    userNotFound: false,
                    duplicateRole: false,
                    error: null
                });
                form.reset();
            }
        });
    }
    
    render() {
        if (this.state.isLoading) {
            return (
                <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            );
        }

        if (this.state.error && !this.state.userNotFound && !this.state.duplicateRole) {
            return (
                <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
                    {JSON.stringify(this.state.error)}
                </div>
            );
        }

        return (
        <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-8">
            <h1 className="font-heading text-2xl font-bold text-foreground mb-6">{this.props.t("Event Role Admin")}</h1>
            
            <div className="bg-white rounded-2xl shadow-sm border border-border p-6 space-y-6">
                <div className="border-b border-border/50 pb-4">
                    <h2 className="text-lg font-semibold text-foreground/90">{this.props.t("Event Role List")}</h2>
                </div>
                <div className="overflow-x-auto rounded-xl border border-border">
                    <table className="min-w-full divide-y divide-border">
                        <thead className="bg-slate-50">
                            <tr>
                                <th scope="col" className="px-6 py-3.5 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">{this.props.t("Role")}</th>
                                <th scope="col" className="px-6 py-3.5 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">{this.props.t("User")}</th>
                                <th scope="col" className="px-6 py-3.5 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">{this.props.t("Actions")}</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-border">
                        {this.state.eventRoles && this.state.eventRoles.map(role => (
                            <tr key={role.id} className="hover:bg-slate-50/50 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-foreground">{role.role}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">{role.user}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                                    <button 
                                        className="inline-flex items-center justify-center p-2 rounded-lg text-sm font-semibold transition-colors bg-error/10 text-error hover:bg-error/20 border border-error/20 cursor-pointer"
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

            <div className="bg-white rounded-2xl shadow-sm border border-border p-6 space-y-6">
                <div className="border-b border-border/50 pb-4">
                    <h2 className="text-lg font-semibold text-foreground/90">{this.props.t("Add Event Role")}</h2>
                </div>
                <form onSubmit={this.onAddRole} className="space-y-4 max-w-xl">
                    <div className="space-y-2">
                        <label htmlFor="email" className="block text-sm font-semibold text-foreground/90">{this.props.t("User Email")}</label>
                        <input 
                            className="w-full border border-border rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                            id="email"
                            type="email"
                            name="email"
                            placeholder={this.props.t("User Email")}
                            required
                        />
                    </div>
                    <div className="space-y-2">
                        <label htmlFor="role" className="block text-sm font-semibold text-foreground/90">{this.props.t("Role")}</label>
                        <select className="w-full border border-border rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all bg-white" id="role" name="role">
                            <option value="admin">{this.props.t("Event Admin")}</option>
                            <option value="reviewer">{this.props.t("Reviewer")}</option>
                            <option value="registration-admin">{this.props.t("Registration Admin")}</option>
                            <option value="registration-volunteer">{this.props.t("Registration Volunteer")}</option>
                            <option value="treasurer">{this.props.t("Event Treasurer")}</option>
                        </select>
                    </div>
                    <div className="pt-2">
                        <button type="submit" className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm">{this.props.t("Add Role")}</button>
                    </div>
                </form>
                {this.state.userNotFound && (
                    <div className="bg-warning/10 text-warning-text border border-warning-border p-4 rounded-xl text-sm mt-3 text-center">
                        {this.props.t("User not found")}
                    </div>
                )}
                {this.state.duplicateRole && (
                    <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm mt-3 text-center">
                        {this.props.t('This user already has this role for this event.')}
                    </div>
                )}
            </div>
        </div>
        );
    }
}

export default withRouter(withTranslation()(EventRoleAdminComponent));