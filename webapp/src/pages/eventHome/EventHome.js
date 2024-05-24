import React, { Component } from "react";
import "./EventHome.css";
import { Route } from "react-router-dom";
import { eventService } from "../../services/events/events.service";
import Application from "../applicationForm";
import ApplicationFormSetting from '../createApplicationForm';
import ReviewForm from '../reviewForm';
import Review from "../review";
import ReviewList from "../reviewList"
import ReviewAssignment from "../reviewAssignment";
import ReviewHistory from "../reviewHistory";
import EventStats from "../eventStats";
import EventConfig from "../eventConfig";
import TagConfig from "../tagConfig";
import ProfileList from "../profileList";
import ViewProfile from "../viewprofile";
import InvitedGuests from "../invitedGuests";
import CreateInvitedGuests from "../createInvitedGuest";
import Registration from "../registration";
import InvitedLetter from "../invitationLetter";
import RegistrationAdmin from "../registrationAdmin";
import Offer from "../offer";
import OfferAdmin from "../offerAdmin";
import { InvoiceAdminList } from "../invoices";
import EventStatus from "../../components/EventStatus";
import { isEventAdmin } from "../../utils/user";
import ResponseList from "../ResponseList/ResponseList";
import ResponsePage from "../ResponsePage/ResponsePage";
import ReviewDashboard from "../reviewDashboard";
import { Attendance, Indemnity } from '../attendance';

class EventInfo extends Component {
  constructor(props) {
    super(props);

    this.state = {
      event: this.props.event,
      error: null,
      offer: null,
      invitedGuest: null,
    };
  }

  render() {
    const { event } = this.state;

    return (
      <div className="event-home">
        <h2>{event.description}</h2>
        <EventStatus longForm={true} event={event} />
        {isEventAdmin(this.props.user, this.props.event) 
        && <EventStats event={this.props.event}/>}
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
      isLoading: true,
    };
  }

  loadEvent = () => {
    const eventKey = this.props.match ? this.props.match.params.eventKey : null;

    this.setState({
      isLoading: true,
    });

    eventService.getByKey(eventKey).then((response) => {
      this.setState(
        {
          event: response.event,
          error: response.error,
          eventKey: eventKey,
          isLoading: false,
        },
        () => {
          this.props.setEvent(eventKey, this.state.event);
        }
      );
    });
  };

  componentDidMount() {
    this.loadEvent();
  }

  render() {
    const { event, error, isLoading } = this.state;
    const { match, organisation } = this.props;

    const loadingStyle = {
      width: "3rem",
      height: "3rem",
    };

    if (isLoading) {
      return (
        <div className="d-flex justify-content-center">
          <div className="spinner-border" style={loadingStyle} role="status">
            <span className="sr-only">Loading...</span>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className={"alert alert-danger alert-container"}>
          {JSON.stringify(error)}
        </div>
      );
    }

    if (!event) {
      return (
        <div className={"alert alert-danger alert-container"}>
          Could not find the event "{this.state.eventKey}"
        </div>
      );
    }

    return (
      <div>
        <Route
          exact
          path={`${match.path}/`}
          render={(props) => <EventInfo {...props} event={event} user={this.props.user}/>}
        />
        <Route
          exact
          path={`${match.path}/responseList`}
          render={(props) => <ResponseList {...props} event={event} user={this.props.user}/>}
        />
        <Route
          exact
          path={`${match.path}/reviewDashboard`}
          render={(props) => <ReviewDashboard {...props} event={event} user={this.props.user}/>}
        />
        <Route
          exact
          path={`${match.path}/invitationLetter`}
          render={(props) => <InvitedLetter {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/apply`}
          render={(props) => <Application {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/apply/new`}
          render={(props) => <Application {...props} event={event} journalSubmissionFlag={true} /> }
        />
        <Route
        exact
          path={`${match.path}/eventAttendance`}
          render={(props) => <Attendance {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/eventConfig`}
          render={(props) => <EventConfig {...props} event={event} organisation={this.props.organisation} />}
        />
        <Route
          exact
          path={`${match.path}/tagConfig`}
          render={(props) => <TagConfig {...props} event={event} organisation={this.props.organisation} />}
        />
        <Route
          exact
          path={`${match.path}/eventStats`}
          render={(props) => <EventStats {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/reviewAssignment`}
          render={(props) => <ReviewAssignment {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/reviewHistory`}
          render={(props) => <ReviewHistory {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/invitedGuests`}
          render={(props) => <InvitedGuests {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/invitedGuests/create`}
          render={(props) => <CreateInvitedGuests {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/review`}
          render={(props) => <Review {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/review/:id`}
          render={(props) => <Review {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/reviewlist`}
          render={(props) => <ReviewList {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/profile-list`}
          render={(props) => <ProfileList {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/offer`}
          render={(props) => <Offer {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/registration`}
          render={(props) => <Registration {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/viewprofile/:id`}
          render={(props) => <ViewProfile {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/registrationAdmin`}
          render={(props) => <RegistrationAdmin {...props} event={event} />}
        />
          <Route
          exact
          path={`${match.path}/responsePage/:id`}
          render={(props) => <ResponsePage {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/applicationform`}
          render={(props) => <ApplicationFormSetting
            {...props}
            event={event}
            languages={organisation && organisation.languages}
            />}
        />
        <Route
          exact
          path={`${match.path}/reviewForm`}
          render={(props) => <ReviewForm
            {...props}
            event={event}
            languages={organisation && organisation.languages}
            />}
        />
        <Route
          exact
          path={`${match.path}/invoices-admin`}
          render={(props) => <InvoiceAdminList {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/indemnity`}
          render={(props) => <Indemnity {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/offerAdmin`}
          render={(props) => <OfferAdmin {...props} event={event} organisation={this.props.organisation}/>}
        />

      </div>
    );
  }
}

export default EventHome;
