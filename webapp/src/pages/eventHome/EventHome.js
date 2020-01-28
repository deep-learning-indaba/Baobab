import React, { Component } from 'react';
import './EventHome.css';
import { applicationFormService } from "../../services/applicationForm";
import { Route, NavLink } from "react-router-dom";
import { eventService } from "../../services/events/events.service";
import Application from "../applicationForm";
import Review from "../review";
import ReviewAssignment from "../reviewAssignment";
import ReviewHistory from "../reviewHistory";
import EventStats from "../eventStats";
import ProfileList from "../profileList";
import ViewProfile from "../viewprofile";
import InvitedGuests from "../invitedGuests";
import CreateInvitedGuests from "../createInvitedGuest";
import Registration from "../registration";
import InvitedLetter from "../invitationLetter";
import RegistrationAdmin from "../registrationAdmin";
import Attendance from "../attendance/Attendance";
import Offer from "../offer";
import { offerServices } from "../../services/offer/offer.service";
import { invitedGuestServices } from "../../services/invitedGuests/invitedGuests.service";

class EventStatus extends Component {
  constructor(props) {
    super(props);

    this.state = {
      applicationStatus: null,
      event: this.props.event,
      error: null,
      offer: null,
      invitedGuest: null
    }
  }

  getApplicationResponse(event_id) {
    applicationFormService.getResponse(event_id).then(resp => {
      let applicationStatus = null;
      if (resp.response) {
        if (resp.response.is_submitted) {
          applicationStatus = "Submitted";
        }
        else if (resp.response.is_withdrawn) {
          applicationStatus = "Withdrawn";
        }
        else {
          applicationStatus = "NOT Submitted";
        }
        this.setState({
          applicationStatus: applicationStatus
        })
      }
      else {
        this.setState({
          applicationStatus: "Not Started"
        });
      }
    });
  }
  
  getOffer(event_id) {
    offerServices.getOffer(event_id).then(result => {
      this.setState({
        offer: result.offer
      });
    });
  }

  getInvitedGuest(event_id) {
    invitedGuestServices.determineIfInvitedGuest(event_id).then(response => {
      if (response.statusCode === "200") {
        this.setState({
          invitedGuest: true
        });
      }
      else if (response.statusCode ==="404"){
        this.setState({
          invitedGuest: false
        });
      }
    });
  }

  componentDidMount() {
    this.getApplicationResponse(this.props.event.id);
    this.getOffer(this.props.event.id);
    this.getInvitedGuest(this.props.event.id);
  }

  render() {
    let statusClass = this.state.applicationStatus === "Submitted" 
      ? this.state.offer === null ? "text-warning" : "text-success" 
      : "text-danger"

    const { event } = this.state
      return (
        <div className="event-home">
          <h1>{event.description}</h1>
  
          {this.state.applicationStatus && 
            <div>
              <div class="status2019 row text-center">
                <div className="col-sm">
                  <h5 className={statusClass}>
  
                    {this.state.applicationStatus === "Submitted" && this.state.offer && <span>
                      Your application was successful! 
                    </span>}
  
                    {this.state.applicationStatus === "Submitted" && !this.state.offer &&  this.state.invitedGuest !== true && <span>
                      Waiting List
                    </span>}
  
                    {this.state.applicationStatus !== "Submitted" && this.state.invitedGuest === true && <span>
                      You've been invited as a guest!
                    </span>}
  
                    {this.state.applicationStatus !== "Submitted" && this.state.invitedGuest !== true && this.state.applicationStatus}
                  </h5>
  
                  { this.state.invitedGuest === true && <div>  
                  <p>You've been invited to {event.description} as a guest! Please proceed to registration <NavLink to="/registration">here</NavLink>.</p>
                  </div>}
  
                  {this.state.applicationStatus === "Submitted" &&
                  <div>
                    {this.state.offer !== null ? <p>There is an offer waiting for you, <NavLink to="/offer">click here</NavLink> to view it.</p>
                    : <p>You are currently on the waiting list for {event.description}. Please await further communication.</p>}
                  </div>}
  
                  {this.state.applicationStatus === "Withdrawn" && <p>
                    Your application has been withdrawn - you will not be considered for a place at {event.description}.
                  </p>}
  
                  {this.state.applicationStatus === "NOT Submitted" && <p>
                    You did not submit an application to attend {event.description}.
                  </p>}
  
                  {this.state.applicationStatus === "Not Started" && this.state.invitedGuest !== true && !this.props.event.is_application_open && <p>
                    You did not apply to attend {event.description}.
                  </p>}

                  {this.state.applicationStatus === "Not Started" && this.state.invitedGuest !== true && this.props.event.is_application_open && <NavLink to={`${this.props.event.key}/apply`} className="btn btn-success">
                      Apply Now!                    
                  </NavLink>}
  
                </div>
              </div>
            </div>
          }
        </div>
      );
    
  }
}

class EventHome extends Component {

  constructor(props) {
    super(props);

    this.state = {
      event: null,
      error: null,
      isLoading: true
    }
  }

  componentDidMount() {
    const { eventKey } = this.props.match.params;

    this.setState({
      isLoading: true
    });

    eventService.getByKey(eventKey).then(response => {
      this.setState({
        event: response.event,
        error: response.error,
        eventKey: eventKey,
        isLoading: false
      }, ()=>{
        this.props.setEvent(eventKey, this.state.event);
      });
    });
  }

  render() {

    const { event, error, isLoading } = this.state;
    const { match } = this.props;

    const loadingStyle = {
      "width": "3rem",
      "height": "3rem"
    }

    if (isLoading) {
        return (
            <div class="d-flex justify-content-center">
            <div class="spinner-border" style={loadingStyle} role="status">
                <span class="sr-only">Loading...</span>
            </div>
            </div>
        );
    }

    if (error) {
      return (
        <div className={"alert alert-danger"}>{JSON.stringify(error)}</div>
      )
    }

    if (! event) {
      return (
      <div className={"alert alert-danger"}>Could not find the event "{this.state.eventKey}"</div>
      )
    }

    return (
      <div>
        <Route 
          exact 
          path={`${match.path}/`}
          render={props => (
            <EventStatus {...props} event={event} />
          )}
        />
        <Route
          exact
          path={`${match.path}/invitationLetter`}
          render={props => (
            <InvitedLetter {...props} event={event} />
          )}
        />
        <Route
          exact
          path={`${match.path}/apply`}
          render={props => (
            <Application {...props} event={event} />
          )}
        />
        <Route
          exact
          path={`${match.path}/eventAttendance`}
          render={props => (
            <Attendance {...props} event={event} />
          )}
        />
        <Route 
          exact 
          path={`${match.path}/eventStats`}
          render={props => (
            <EventStats {...props} event={event} />
          )}
        />
        <Route
          exact
          path={`${match.path}/reviewAssignment`}
          render={props => (
            <ReviewAssignment {...props} event={event} />
          )}
        />
        <Route
          exact
          path={`${match.path}/reviewHistory`}
          render={props => (
            <ReviewHistory {...props} event={event} />
          )}
        />
        <Route
          exact
          path={`${match.path}/invitedGuests`}
          render={props => (
            <InvitedGuests {...props} event={event} />
          )}
        />
        <Route
          exact
          path={`${match.path}/invitedGuests/create`}
          render={props => (
            <CreateInvitedGuests {...props} event={event} />
          )}
        />
        <Route 
          exact 
          path={`${match.path}/review`}
          render={props => (
            <Review {...props} event={event} />
          )}
        />
        <Route 
          exact 
          path={`${match.path}/review/:id`}
          render={props => (
            <Review {...props} event={event} />
          )}
        />
        <Route
          exact
          path={`${match.path}/profile-list`}
          render={props => (
            <ProfileList {...props} event={event} />
          )}
        />
        <Route 
          exact 
          path={`${match.path}/offer`}
          render={props => (
            <Offer {...props} event={event} />
          )}
        />
        <Route
          exact
          path={`${match.path}/registration`}
          render={props => (
            <Registration {...props} event={event} />
          )}
        />
        <Route
          exact
          path={`${match.path}/viewprofile/:id`}
          render={props => (
            <ViewProfile {...props} event={event} />
          )}
        />
        <Route
          exact
          path={`${match.path}/registrationAdmin`}
          render={props => (
            <RegistrationAdmin {...props} event={event} />
          )}
        />
        </div>
    )
    
  }
}

export default EventHome;
