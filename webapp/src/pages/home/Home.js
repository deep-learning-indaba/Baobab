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
                        upcomingEvents: response.events.filter(e => e.event_type === 'EVENT' && (e.is_event_opening || e.is_event_open)),
                        awards: response.events.filter(e => e.event_type === 'AWARD'  && (e.is_event_opening || e.is_event_open)),
                        calls: response.events.filter(e => e.event_type === "CALL"  && (e.is_event_opening || e.is_event_open)),
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

    renderEventTable = (events, description) => {
        if (this.props.user && events && events.length > 0) {
            return (<div className="row event-table-container">
                <div className="col">
                    <h3 className="text-center">{this.props.t(description)}</h3>
                    <div class="card">
                        <table className="event-table">
                            <tbody>
                                {events.map(e => {
                                    return (<tr key={e.key}>
                                        <td>
                                            <h5 className="text-left"><NavLink to={`/${e.key}`}>{e.description}</NavLink></h5>
                                            <span className="text-left">{e.start_date + " to " + e.end_date}</span>
                                        </td>
                                        <td>{this.statusDisplay(e)}</td>
                                    </tr>)
                                })}
                            </tbody>
                    </table>
                    </div>
                </div>
            </div>);
        }
        return <div></div>
    }

    render() {
        const t = this.props.t;
        let logo = this.state.organisation && this.state.organisation.large_logo;
        // TODO: Remove this terrible hack once we have OrganisationTranslation on the backend
        if (this.state.organisation) {
            console.log("this.state.organisation.name:", this.state.organisation.name);
            console.log("this.props.i18n.language:", this.props.i18n.language);
        }
        
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
                            <h2 className="Blurb">{t("Welcome to") + " "} {this.state.organisation.system_name}</h2>}
                        <p><NavLink to="/createAccount" id="nav-signup">{t("Sign Up")}</NavLink> {t("for an account in order to apply for an event, award or call for proposals")}. <NavLink id="nav-login" to="/login">{t("Sign In")}</NavLink> {t("if you already have one")}.</p>
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
