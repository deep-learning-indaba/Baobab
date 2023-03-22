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
            journals: null,
            continuous_journals: null,
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
                        upcomingEvents: response.events.filter(e => e.event_type === 'EVENT' && (e.is_event_opening || e.is_event_open)),
                        awards: response.events.filter(e => e.event_type === 'AWARD'  && (e.is_event_opening || e.is_event_open)),
                        journals: response.events.filter(e => e.event_type === 'JOURNAL'&& (e.is_event_opening || e.is_event_open)),
                        continuous_journals: response.events.filter(e => e.event_type === 'CONTINUOUS_JOURNAL'),
                        calls: response.events.filter(e => e.event_type === "CALL"  && (e.is_event_opening || e.is_event_open)),
                        programmes: response.events.filter(e => e.event_type === "PROGRAMME"  && (e.is_event_opening || e.is_event_open)),
                        attended: response.events.filter(e => !e.is_event_opening)
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

    dateDisplay = (e) => {
        if (e.event_type === 'EVENT') {
            return `${e.start_date} to ${e.end_date}`;
        }
        if (e.event_type === 'CONTINUOUS_JOURNAL') {
            return `Rolling Submissions`;
        }
        else {
            return this.props.t("Applications Close") + " " + e.application_close_date;
        }
    }

    renderEventTable = (events, description) => {
        if (this.props.user && events && events.length > 0) {
            return (
                <div className="event-table-container">
                    <h3 className="text-center">{this.props.t(description)}</h3>
                    <div className="custom-card">
                           {events.map(e => {
                                return (
                                    <div className="event" key={e.key}>
                                        <div className="event-info">
                                            <h5><NavLink to={`/${e.key}`}>{e.description}</NavLink></h5>
                                            {this.dateDisplay(e)}
                                        </div>
                                        <div className="status-holder">{this.statusDisplay(e)}</div>
                                    </div>
                                )
                            })}
                    </div>
                </div>
            );
        }
        return <div></div>
    }
    
    render() {
        const t = this.props.t;
        let logo = this.state.organisation && this.state.organisation.large_logo;
        // TODO: Remove this terrible hack once we have OrganisationTranslation on the backend
        if (this.state.organisation && this.state.organisation.name === "AI4D Africa" && this.props.i18n.language === "fr") {
            logo = "ai4d_logo_fr.png";
        }

        return (
            <div>
                <div>
                    <img src={this.state.organisation &&
                        require("../../images/" + logo)}
                        className="img-fluid large-logo" alt="logo" />
                </div>

                {!this.props.user &&
                    <div className="text-center">
                        {this.state.organisation &&
                            <h2 className="Blurb text-center">{t("Welcome to") + " "} {this.state.organisation.system_name}</h2>}
                        <p className="text-center"><NavLink to="/createAccount" id="nav-signup">{t("Sign Up")}</NavLink> {t("for an account in order to apply for an event, award or call for proposals")}. <NavLink id="nav-login" to="/login">{t("Sign In")}</NavLink> {t("if you already have one")}.</p>
                    </div>
                }

                {this.props.user && this.props.user.is_admin &&
                    <a href="../eventConfig" id="new_event_button" name="new_event_button" className="btn btn-primary">{this.props.t("Create New Event")}</a>
                }

                {this.renderEventTable(this.state.upcomingEvents, "Upcoming Events")}
                {this.renderEventTable(this.state.awards, "Awards")}
                {this.renderEventTable(this.state.journals, "Journals")}
                {this.renderEventTable(this.state.continuous_journals, "Continuous Journals")}
                {this.renderEventTable(this.state.calls, "Calls for Proposals")}
                {this.renderEventTable(this.state.programmes, "Programmes")}
                {this.renderEventTable(this.state.attended, "Past Events")}



            </div >)
    }
}

export default withTranslation()(Home);
