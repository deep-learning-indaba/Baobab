import React, { Component } from "react";
import "./EventHome.css";
import { Route } from "react-router-dom";
import { eventService } from "../../services/events/events.service";
import Application from "../applicationForm";
import Review from "../review";
import ReviewAssignment from "../reviewAssignment";
import ReviewHistory from "../reviewHistory";
import EventStats from "../eventStats";
import EventConfig from "../eventConfig";
import ProfileList from "../profileList";
import ViewProfile from "../viewprofile";
import InvitedGuests from "../invitedGuests";
import CreateInvitedGuests from "../createInvitedGuest";
import Registration from "../registration";
import InvitedLetter from "../invitationLetter";
import RegistrationAdmin from "../registrationAdmin";
import Attendance from "../attendance/Attendance";
import Offer from "../offer";
import EventStatus from "../../components/EventStatus";

class MiniConf extends Component {
  constructor(props) {
    super(props);

    this.state = {
      event: this.props.event,
    };
  }

  showMiniConf = (event) => {
    var currentdate = new Date();
    if (
      event.miniconf_url &&
      event.status &&
      (event.status.invited_guest ||
        event.status.offer_status === "Accepted") &&
      new Date(event.start_date) <= currentdate &&
      currentdate <= new Date(event.end_date)
    ) {
      return (
        <div>
          Connect to{" "}
          <a
            href={
              "https://" +
              event.miniconf_url +
              "/index.html?token=" +
              JSON.parse(localStorage.getItem("user"))["token"] +
              "&organisation_id=" +
              event.organisation_id +
              "&redirect_back_url=" +
              window.location.href +
              "&verify_token_url=" +
              process.env.REACT_APP_API_URL +
              "/api/v1/validate-user-for-organization" +
              "&origin=" +
              window.location.origin
            }
          >
            mini-conf
          </a>{" "}
          .{" "}
        </div>
      );
    }
    return <div />;
  };

  render() {
    const { event } = this.state;
    return this.showMiniConf(event);
  }
}

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
        <h1>{event.description}</h1>
        <EventStatus longForm={true} event={event} />
        <MiniConf event={event} />
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
    const { match } = this.props;

    const loadingStyle = {
      width: "3rem",
      height: "3rem",
    };

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
          render={(props) => <EventInfo {...props} event={event} />}
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
          path={`${match.path}/eventAttendance`}
          render={(props) => <Attendance {...props} event={event} />}
        />
        <Route
          exact
          path={`${match.path}/eventConfig`}
          render={(props) => <EventConfig {...props} event={event} />}
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
      </div>
    );
  }
}

export default EventHome;
