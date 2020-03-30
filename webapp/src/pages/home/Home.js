import React, { Component } from 'react';
import './Home.css';
import { NavLink } from "react-router-dom";
import { eventService } from "../../services/events/events.service";
import { organisationService } from "../../services/organisation/organisation.service";


class Home extends Component {

    constructor(props) {
        super(props);
        this.state = {
            upcomingEvents: null,
            awards: null,
            organisation: null,
            errors: []
        }
    }

    componentDidMount() {
        if (this.props.user) {
            eventService.getEvents().then(response => {
                if (response.error) {
                    this.setState(prevState => ({
                        errors: [
                            ...prevState.errors,
                            response.error
                        ]
                    }));
                }
                if (response.events) {
                    this.setState({
                        upcomingEvents: response.events.filter(e => e.event_type === 'EVENT'),
                        awards: response.events.filter(e => e.event_type === 'AWARD')
                    });
                }
            });
        }

        if (this.props.setEvent) {
            this.props.setEvent(null, null);
        }

        organisationService.getOrganisation().then(response => {
            if (response.error) {
                this.setState(prevState => ({
                    errors: [
                        ...prevState.errors,
                        response.error
                    ]
                }));
            }
            this.setState({
                organisation: response.organisation,
            });
        });
    }

    statusDisplay(e) {
        if (e.status === "Apply now" && e.is_application_open) {
            return <NavLink to={`${e.key}/apply`} className="btn btn-success">Apply Now</NavLink>
        } else if (e.status === "Continue application" && e.is_application_open) {
            return <NavLink to={`${e.key}/apply`} className="btn btn-warning">Continue Application</NavLink>
        } else if (e.status === "Application withdrawn" && e.is_application_open) {
            return <div>
                Application Withdrawn<br />
                <NavLink to={`${e.key}/apply`} className="btn btn-warning">Re-apply</NavLink>
            </div>
        } else {
            return e.status
        }
    }

    render() {
        return (
            <div>
                <div>
                    <img src={this.state.organisation &&
                        require("../../images/" +
                            this.state.organisation.large_logo)}
                        className="img-fluid large-logo" alt="logo" />
                </div>

                {!this.props.user &&
                    <div>
                        {this.state.organisation &&
                            <h2 className="Blurb">Welcome to {this.state.organisation.system_name}</h2>}
                        <p class="text-center"><NavLink to="/createAccount">Sign up</NavLink> for an account in order to apply for an event, or <NavLink to="/login">login</NavLink> if you already have one.</p>
                    </div>
                }

                {this.props.user &&
                    <div>
                        <table className="event-table">
                            {this.state.upcomingEvents &&
                                this.state.upcomingEvents.length > 0 &&
                                <thead><tr><th colspan="2"><br /><br /><h3 className="text-center">Upcoming Events</h3></th></tr></thead>}
                            {this.state.upcomingEvents &&
                                this.state.upcomingEvents.length > 0 &&
                                <tbody>
                                    {this.state.upcomingEvents.map(e => {
                                        // TODO: Update status based on event stage changes.
                                        return (<tr>
                                            <td>
                                                <h5><NavLink to={`/${e.key}`}>{e.description}</NavLink></h5>
                                                {e.start_date + " to " + e.end_date}
                                            </td>
                                            <td>{this.statusDisplay(e)}</td>
                                        </tr>)
                                    })}
                                </tbody>
                            }
                            {this.state.awards &&
                                this.state.awards.length > 0 &&
                                <thead><tr><th colspan="2"><br /><h3 className="text-center">Awards</h3></th></tr></thead>}
                            {this.state.awards &&
                                this.state.awards.length > 0 &&
                                <tbody>
                                    {this.state.awards.map(e => {
                                        // TODO: Update status based on event stage changes.
                                        return (<tr>
                                            <td>
                                                <h5><NavLink to={`/${e.key}`}>{e.description}</NavLink></h5>
                                                {e.start_date + " to " + e.end_date}
                                            </td>
                                            <td>{this.statusDisplay(e)}</td>
                                        </tr>)
                                    })}
                                </tbody>
                            }

                        </table>

                    </div>}
            </div>
        );
    }
}

export default Home;
