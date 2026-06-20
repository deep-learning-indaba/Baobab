import EventNav from '../../components/EventNav';
import React, { Component } from "react";
import { Route } from "react-router-dom";
import { eventService } from "../../services/events/events.service";
import Application from "../applicationForm";
import ApplicationFormSetting from '../createApplicationForm';
import ReviewForm from '../reviewForm';
import FormEditorPage from '../formEditorPage';
import FormPage from '../formPage';
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
import { attendanceService } from '../../services/attendance';
import ResponseList from "../ResponseList/ResponseList";
import ResponsePage from "../ResponsePage/ResponsePage";
import ReviewDashboard from "../reviewDashboard";
import { Attendance, Indemnity } from '../attendance';
import EventRoleAdmin from "../eventRoleAdmin";
import FormManagement from "../formManagement";
import FormPreviewPage from "../formPreview";
import FormResponseList from "../formResponseList";
import FormResponseDetail from "../formResponseDetail";
import ApplicationFormResponsePage from "../applicationFormResponse";
import FormConfigPage from "../formConfig";
import { Card } from '../../components/ui/card';
import { EventAppHome, EventAppProgramme, ProgrammeEditor, EventAppAnnouncements, AnnouncementDetail, AnnouncementsAdmin, MyTicket, CheckinConsole, BadgeExport, MyProfile, ViewMemberProfile, ProfileBrowser, ScanConnect, Connections, ConnectLanding } from '../eventApp';
import ConsentGate from '../../components/ConsentGate';

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
      <div className="py-6 max-w-5xl mx-auto space-y-8">
        <Card className="p-8 rounded-2xl shadow-sm border border-border bg-white">
          <h1 className="font-heading text-3xl font-bold text-foreground mb-6 pb-6 border-b border-border/50">
            {event.description}
          </h1>
          <div>
            <EventStatus longForm={true} event={event} />
          </div>
        </Card>

        {isEventAdmin(this.props.user, this.props.event) && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-foreground px-1">Admin Dashboard</h2>
            <EventStats event={this.props.event} />
          </div>
        )}
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
      sidebarOpen: false,
      isConfirmedGuest: false,
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
          if (this.state.event) {
            this.loadConfirmedGuest(this.state.event.id);
          }
        }
      );
    });
  };

  loadConfirmedGuest = (eventId) => {
    if (!this.props.user || !eventId) {
      return;
    }
    attendanceService.isConfirmedGuest(eventId).then(result => {
      this.setState({ isConfirmedGuest: result.isConfirmedGuest });
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
    const { sidebarOpen } = this.state;
    const closeSidebar = () => this.setState({ sidebarOpen: false });

    const sidebarClass = `event-sidebar${sidebarOpen ? ' event-sidebar--open' : ''}`;

    return (
      <div className="flex h-[calc(100vh-64px)] overflow-hidden bg-[#f8f9fa] -mx-4 md:-mx-8 -mt-8 -mb-8 md:-mb-12">
        {/* Backdrop — mobile only, shown when drawer is open */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/40 z-30 md:hidden"
            onClick={closeSidebar}
          />
        )}

        {/* Sidebar */}
        <div className={sidebarClass}>
          {/* Mobile close button */}
          <div className="mobile-only justify-end mb-2 -mr-1">
            <button
              className="p-1.5 rounded-lg text-foreground/60 hover:bg-surface-high hover:text-foreground transition-colors"
              onClick={closeSidebar}
              aria-label="Close menu"
            >
              <i className="fas fa-times" style={{ fontSize: 18 }} />
            </button>
          </div>
          <EventNav
            eventKey={this.state.eventKey}
            event={event}
            user={this.props.user}
            organisation={organisation}
            onClose={closeSidebar}
            isConfirmedGuest={this.state.isConfirmedGuest}
          />
        </div>

        <div className="flex-1 overflow-y-auto py-8 px-4 md:px-8 max-w-[1200px] min-w-0">
          {/* Mobile hamburger button */}
          <button
            className="mobile-only items-center gap-2 mb-6 px-3 py-2 rounded-lg bg-white border border-border shadow-sm text-sm font-medium text-foreground hover:bg-surface-low transition-colors"
            onClick={() => this.setState({ sidebarOpen: true })}
            aria-label="Open menu"
          >
            <i className="fas fa-bars" style={{ fontSize: 16 }} />
            Menu
          </button>
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
        <Route
          exact
          path={`${match.path}/eventRoleAdmin`}
          render={(props) => <EventRoleAdmin {...props} event={event} organisation={this.props.organisation}/>}
        />
        <Route
          exact
          path={`${match.path}/formManagement`}
          render={(props) => <FormManagement {...props} event={event} user={this.props.user}/>}
        />
        <Route
          exact
          path={`${match.path}/formConfig`}
          render={(props) => <FormConfigPage {...props} event={event} user={this.props.user} eventKey={this.state.eventKey}/>}
        />
        <Route
          exact
          path={`${match.path}/forms/new`}
          render={(props) => (
            <FormEditorPage
              {...props}
              eventKey={this.state.eventKey}
              event={event}
              organisation={this.props.organisation}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/forms/:formId/edit`}
          render={(props) => (
            <FormEditorPage
              {...props}
              eventKey={this.state.eventKey}
              event={event}
              organisation={this.props.organisation}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/form-responses/:formId/:responseId`}
          render={(props) => {
            const formId = parseInt(props.match.params.formId, 10);
            if (event && event.application_form_id === formId) {
              return (
                <ApplicationFormResponsePage
                  {...props}
                  event={event}
                  user={this.props.user}
                />
              );
            }
            return (
              <FormResponseDetail
                {...props}
                event={event}
                user={this.props.user}
              />
            );
          }}
        />
        <Route
          exact
          path={`${match.path}/form-responses/:formId`}
          render={(props) => (
            <FormResponseList
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/forms/:formId/preview`}
          render={(props) => (
            <FormPreviewPage
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/forms/:formId`}
          render={(props) => (
            <FormPage
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/event-app`}
          render={(props) => (
            <EventAppHome
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/event-app/programme`}
          render={(props) => (
            <EventAppProgramme
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/programmeEditor`}
          render={(props) => (
            <ProgrammeEditor
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/event-app/announcements`}
          render={(props) => (
            <EventAppAnnouncements
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/event-app/announcements/:announcementId`}
          render={(props) => (
            <AnnouncementDetail
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/announcementsAdmin`}
          render={(props) => (
            <AnnouncementsAdmin
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/app/ticket`}
          render={(props) => (
            <MyTicket
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/checkin`}
          render={(props) => (
            <CheckinConsole
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/checkin/badges`}
          render={(props) => (
            <BadgeExport
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/app/profile`}
          render={(props) => (
            <MyProfile
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/app/profile/:userId`}
          render={(props) => (
            <ViewMemberProfile
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/app/community`}
          render={(props) => (
            <ProfileBrowser
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/app/scan`}
          render={(props) => (
            <ScanConnect
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/app/connections`}
          render={(props) => (
            <Connections
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <Route
          exact
          path={`${match.path}/connect`}
          render={(props) => (
            <ConnectLanding
              {...props}
              event={event}
              user={this.props.user}
            />
          )}
        />
        <ConsentGate event={event} />
        </div>
      </div>
    );
  }
}

export default EventHome;
