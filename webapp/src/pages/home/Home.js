import React, { Component } from 'react';
import './Home.css';
import { NavLink } from "react-router-dom";
import { eventService } from "../../services/events/events.service";
import { organisationService } from "../../services/organisation/organisation.service";
import EventStatus from "../../components/EventStatus";
import { withTranslation } from 'react-i18next';


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
                        awards: response.events.filter(e => e.event_type === 'AWARD'),
                        calls: response.events.filter(e => e.event_type == "CALL"),
                        attended: response.events.filter(e => e.event_type == "ATTENDED")
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
        return <EventStatus longForm={false} event={e} />;
    }

    renderEventTable = (events, description) => {
        if (this.props.user && events && events.length > 0) {
            return (<div class="event-table-container">
                <h3 className="text-center">{this.props.t(description)}</h3>
                <div class="card">
                    <table className="event-table">
                        <tbody>
                            {events.map(e => {
                                return (<tr>
                                    <td>
                                        <h5><NavLink to={`/${e.key}`}>{e.description}</NavLink></h5>
                                        {e.start_date + " to " + e.end_date}
                                    </td>
                                    <td>{this.statusDisplay(e)}</td>
                                </tr>)
                            })}
                        </tbody>
                </table>
                </div>
            </div>);
        }
        return <div></div>
    }

    render() {
        const t = this.props.t;

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
                            <h2 className="Blurb">{t("Welcome to") + " "} {this.state.organisation.system_name}</h2>}
                        <p class="text-center"><NavLink to="/createAccount" id="nav-signup">{t("Sign Up")}</NavLink> {t("for an account in order to apply for an event, award or call for proposals")}. <NavLink id="nav-login" to="/login">{t("Sign In")}</NavLink> {t("if you already have one")}.</p>
                    </div>
                }

                {this.renderEventTable(this.state.upcomingEvents, "Upcoming Events")}
                {this.renderEventTable(this.state.awards, "Awards")}
                {this.renderEventTable(this.state.calls, "Calls for Proposals")}
                {this.renderEventTable(this.state.attended, "Past Events")}

            </div >)
    }
}

export default withTranslation()(Home);
