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
            errors: [],
         
        };
    };

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
                };
                if (response.events) {
                    this.setState({
                        upcomingEvents: response.events.filter(e => e.event_type === 'EVENT' && (e.is_event_opening || e.is_event_open)),
                        awards: response.events.filter(e => e.event_type === 'AWARD' && (e.is_event_opening || e.is_event_open)),
                        calls: response.events.filter(e => e.event_type === "CALL" && (e.is_event_opening || e.is_event_open)),
                        attended: response.events.filter(e => !e.is_event_opening)
                    });
                };
            });
        };

        if (this.props.setEvent) {
            this.props.setEvent(null, null);
        };

        organisationService.getOrganisation().then(response => {
            if (response.error) {
                this.setState(prevState => ({
                    errors: [
                        ...prevState.errors,
                        response.error
                    ]
                }));
            };
            this.setState({
                organisation: response.organisation,
            });
        });
    };



    // Status Display
    statusDisplay(e) {
        return <EventStatus longForm={false} event={e} />;
    }

    // Render Event Table
    renderEventTable = (events, description) => {
        if (this.props.user && events && events.length > 0) {
            return (
                <div className="event-table-container">
                    <h3 className="text-center">{this.props.t(description)}</h3>
                    <div className="card">

                        <table className="event-table">
                            <tbody>
                                {events.map(e => {
                                    return (<tr key={e.key}>
                                        <td>
                                            <h5><NavLink to={`/${e.key}`}>{e.description}</NavLink></h5>
                                            {e.start_date + " to " + e.end_date}
                                        </td>
                                        <td>{this.statusDisplay(e)}</td>
                                    </tr>)
                                })}
                                 {this.renderAddEvent()}
                            </tbody>
                        </table>
                    </div>
                </div>);
        };
        return <div></div>
    };

    renderAddEvent() {
        const t = this.props.t;

        if (this.props.user && this.props.user.is_admin ) {
            return (
                <div>
                    <button className="btn btn-secondary">
                    <NavLink className to="/newEvent">{t(`Add Event`)}</NavLink>
                    </button>
                </div>
            )
        };
    };


    render() {
        const {
            organisation,
            upcomingEvents,
            awards,
            calls,
            attended,
            open
        } = this.state;

        const t = this.props.t;

        let logo = organisation && organisation.large_logo;
        // TODO: Remove this terrible hack once we have OrganisationTranslation on the backend
        if (this.state.organisation) {
            console.log("this.state.organisation.name:", this.state.organisation.name);
            console.log("this.props.i18n.language:", this.props.i18n.language);
        }

        if (organisation && organisation.name === "AI4D Africa" && this.props.i18n.language === "fr") {
            logo = "ai4d_logo_fr.png";
        }

        return (
            <div>
                <div>
                    <img src={organisation &&
                        require("../../images/" + logo)}
                        className="img-fluid large-logo" alt="logo" />
                </div>

                {!this.props.user &&
                    <div className="text-center">
                        {organisation &&
                            <h2 className="Blurb text-center">{t("Welcome to") + " "} {organisation.system_name}</h2>}
                        <p className="text-center"><NavLink to="/createAccount" id="nav-signup">{t("Sign Up")}</NavLink> {t("for an account in order to apply for an event, award or call for proposals")}. <NavLink id="nav-login" to="/login">{t("Sign In")}</NavLink> {t("if you already have one")}.</p>
                    </div>
                }

                {this.renderEventTable(upcomingEvents, "Upcoming Events")}
                {this.renderEventTable(awards, "Awards")}
                {this.renderEventTable(calls, "Calls for Proposals")}
                {this.renderEventTable(attended, "Past Events")}

               

       
            </div >
        )
    }
}

export default withTranslation()(Home);
