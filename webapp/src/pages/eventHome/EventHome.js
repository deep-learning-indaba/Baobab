import EventNav from '../../components/EventNav';
import React, { Component } from "react";
import { Link, Route } from "react-router-dom";
import { eventService } from "../../services/events/events.service";
import { announcementService } from "../../services/eventApp/announcement.service";
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
import { withTranslation, useTranslation } from 'react-i18next';
import { useInstall } from '../../context/InstallContext';
import { EventAppProgramme, ProgrammeEditor, EventAppAnnouncements, AnnouncementDetail, AnnouncementsAdmin, MyTicket, CheckinConsole, BadgeExport, MyProfile, ViewMemberProfile, ProfileBrowser, ScanConnect, Connections, ConnectLanding } from '../eventApp';
import EventDashboard from '../eventDashboard';
import ResourceLinksAdmin from '../resourceLinks';
import ConsentGate from '../../components/ConsentGate';

function iconCls(icon) {
  if (!icon) return null;
  if (icon.includes(' ')) return icon;
  if (icon.startsWith('fa')) return `fas ${icon}`;
  return null;
}

const TILE_CLS = "flex flex-col items-center justify-center gap-2 p-4 min-h-[96px] bg-white rounded-xl border border-border hover:bg-primary/5 hover:border-primary/20 transition-colors";

const QuickTile = ({ to, icon, label, external }) => {
  const inner = <>
    <i className={`${icon} text-primary text-2xl`} />
    <span className="text-xs font-semibold text-foreground text-center leading-tight">{label}</span>
  </>;
  return external
    ? <a href={to} target="_blank" rel="noopener noreferrer" className={TILE_CLS}>{inner}</a>
    : <Link to={to} className={TILE_CLS}>{inner}</Link>;
};

const DOT_PATTERN = {
  backgroundImage: 'radial-gradient(#c8d5c4 1px, transparent 1px)',
  backgroundSize: '16px 16px',
};

class EventInfo extends Component {
  constructor(props) {
    super(props);
    this.state = {
      links: [],
      announcements: [],
      appContentLoaded: false,
      countdown: null,
    };
    this.countdownTimer = null;
  }

  componentDidMount() {
    if (!this.props.isConfirmedGuest) return;
    if (this.props.event.start_date) this.startCountdown(this.props.event.start_date);
    this.loadAppContent();
  }

  componentDidUpdate(prevProps) {
    if (!prevProps.isConfirmedGuest && this.props.isConfirmedGuest) {
      if (this.props.event.start_date) this.startCountdown(this.props.event.start_date);
      this.loadAppContent();
    }
  }

  componentWillUnmount() {
    if (this.countdownTimer) clearInterval(this.countdownTimer);
  }

  startCountdown(startDateStr) {
    const update = () => this.setState({ countdown: this.computeCountdown(startDateStr) });
    update();
    this.countdownTimer = setInterval(update, 60000);
  }

  computeCountdown(startDateStr) {
    const target = new Date(startDateStr);
    if (isNaN(target.getTime())) return null;
    const diff = target.getTime() - Date.now();
    if (diff <= 0) return null;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return { days, hours, mins };
  }

  loadAppContent() {
    const { event, i18n } = this.props;
    const language = (i18n && i18n.language) || 'en';
    Promise.all([
      eventService.getResourceLinks(event.id, language),
      announcementService.listActive(event.id, language),
    ]).then(([linksResult, announcementsResult]) => {
      this.setState({
        links: linksResult.links || [],
        announcements: announcementsResult.data || [],
        appContentLoaded: true,
      });
    });
  }

  headerStatus() {
    const { event, t } = this.props;
    const s = event.status;
    if (!s) return null;

    if (s.registration_status === 'Confirmed') {
      return {
        label: t('Registered'), labelCls: 'text-green-700', icon: 'fa-check-circle',
        action: { to: `/${event.key}/app/ticket`, label: t('View Ticket') },
      };
    }
    if (s.registration_status === 'Not Confirmed') {
      return { label: t('Pending Confirmation'), labelCls: 'text-amber-600', icon: 'fa-clock', action: null };
    }
    if (event.is_registration_open) {
      return {
        label: t('Registration Required'), labelCls: 'text-amber-600', icon: 'fa-exclamation-circle',
        action: { to: `/${event.key}/registration`, label: t('Register Now') },
      };
    }
    if (event.is_event_open && s.is_event_attendee) {
      return { label: t('Now Live'), labelCls: 'text-green-700', icon: 'fa-circle', action: null };
    }
    return { label: t('Confirmed'), labelCls: 'text-green-700', icon: 'fa-check-circle', action: null };
  }

  render() {
    const { event, isConfirmedGuest, t } = this.props;
    const { links, announcements, appContentLoaded, countdown } = this.state;
    const eventKey = event && event.key;
    const status = isConfirmedGuest ? this.headerStatus() : null;

    return (
      <div className="py-6 max-w-5xl mx-auto space-y-5">

        {/* Header */}
        {isConfirmedGuest ? (
          <div className="rounded-xl border border-border overflow-hidden bg-white" style={DOT_PATTERN}>
            <div className="bg-white/80 backdrop-blur-sm p-6 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              <div className="min-w-0">
                {status && (
                  <p className={`text-xs font-bold uppercase tracking-widest mb-1.5 flex items-center gap-1.5 ${status.labelCls}`}>
                    <i className={`fas ${status.icon}`} />
                    {status.label}
                  </p>
                )}
                <h1 className="font-heading text-2xl font-bold text-foreground leading-tight">{event.name}</h1>
                {event.description && event.description !== event.name && (
                  <p className="text-sm text-muted-foreground mt-1">{event.description}</p>
                )}
                {status && status.action && (
                  <div className="mt-3">
                    <Link
                      to={status.action.to}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm"
                    >
                      {status.action.label}
                      <i className="fas fa-arrow-right text-xs" />
                    </Link>
                  </div>
                )}
              </div>
              {(countdown || event.start_date) && (
                <div className="shrink-0 bg-primary/10 border border-primary/20 rounded-lg px-4 py-3 text-center space-y-3">
                  {countdown && (
                    <div>
                      <p className="text-xs font-bold text-primary uppercase tracking-wide mb-2">{t('Starts in')}</p>
                      <div className="flex items-center gap-2">
                        <div className="text-center">
                          <span className="block text-xl font-bold text-primary leading-none">{String(countdown.days).padStart(2, '0')}</span>
                          <span className="block text-[10px] font-bold text-muted-foreground uppercase tracking-wide mt-0.5">{t('Days')}</span>
                        </div>
                        <span className="text-primary font-bold pb-4">:</span>
                        <div className="text-center">
                          <span className="block text-xl font-bold text-primary leading-none">{String(countdown.hours).padStart(2, '0')}</span>
                          <span className="block text-[10px] font-bold text-muted-foreground uppercase tracking-wide mt-0.5">{t('Hrs')}</span>
                        </div>
                        <span className="text-primary font-bold pb-4">:</span>
                        <div className="text-center">
                          <span className="block text-xl font-bold text-primary leading-none">{String(countdown.mins).padStart(2, '0')}</span>
                          <span className="block text-[10px] font-bold text-muted-foreground uppercase tracking-wide mt-0.5">{t('Mins')}</span>
                        </div>
                      </div>
                    </div>
                  )}
                  {event.start_date && (
                    <div className={countdown ? 'border-t border-primary/20 pt-3' : ''}>
                      <p className="text-xs font-bold text-primary uppercase tracking-wide mb-1">{t('Event Dates')}</p>
                      <p className="text-sm font-semibold text-foreground">{event.start_date}</p>
                      {event.end_date && event.end_date !== event.start_date && (
                        <p className="text-sm font-semibold text-foreground">{event.end_date}</p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-border p-8">
            <h1 className="font-heading text-3xl font-bold text-foreground mb-6 pb-6 border-b border-border/50">
              {event.description}
            </h1>
            <EventStatus longForm={true} event={event} />
          </div>
        )}

        {/* Quick links */}
        {isConfirmedGuest && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <QuickTile to={`/${eventKey}/app/ticket`}          icon="fas fa-ticket-alt"  label={t('My Ticket')} />
            <QuickTile to={`/${eventKey}/app/profile`}         icon="fas fa-user"         label={t('My Profile')} />
            <QuickTile to={`/${eventKey}/app/scan`}            icon="fas fa-qrcode"       label={t('Scan Badge')} />
            <QuickTile to={`/${eventKey}/event-app/programme`} icon="fas fa-calendar-alt" label={t('Programme')} />
          </div>
        )}

        {/* Resource links */}
        {isConfirmedGuest && appContentLoaded && links.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest px-0.5">{t('Resources')}</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {links.map(link => {
                const cls = iconCls(link.icon);
                const isEmoji = link.icon && !cls;
                return (
                  <a
                    key={link.id}
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={TILE_CLS}
                  >
                    {cls
                      ? <i className={`${cls} text-primary text-2xl`} />
                      : isEmoji
                        ? <span className="text-2xl leading-none">{link.icon}</span>
                        : <i className="fas fa-link text-primary text-2xl" />
                    }
                    <span className="text-xs font-semibold text-foreground text-center leading-tight line-clamp-2">{link.title}</span>
                  </a>
                );
              })}
            </div>
          </div>
        )}

        {/* Announcements */}
        {isConfirmedGuest && appContentLoaded && announcements.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between px-0.5">
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest">{t('Announcements')}</p>
              <Link to={`/${eventKey}/event-app/announcements`} className="text-xs font-semibold text-primary hover:underline">
                {t('See all')} &rarr;
              </Link>
            </div>
            <div className="bg-white rounded-xl border border-border overflow-hidden">
              {announcements.slice(0, 3).map((ann, i) => (
                <Link
                  key={ann.id}
                  to={`/${eventKey}/event-app/announcements/${ann.id}`}
                  className={`flex items-start gap-4 px-4 py-3.5 hover:bg-primary/5 transition-colors group${i > 0 ? ' border-t border-border' : ''}`}
                >
                  <div className={`w-0.5 self-stretch rounded-full shrink-0 ${i === 0 ? 'bg-primary' : 'bg-border'}`} />
                  <div className="min-w-0 flex-1 py-0.5">
                    <p className="text-sm font-semibold text-foreground leading-snug">{ann.title}</p>
                    {ann.body_markdown && (
                      <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">{ann.body_markdown}</p>
                    )}
                  </div>
                  <i className="fas fa-chevron-right text-border text-xs mt-1.5 shrink-0 group-hover:text-primary transition-colors" />
                </Link>
              ))}
            </div>
          </div>
        )}

        <InstallHint />
      </div>
    );
  }
}

function InstallHint() {
  const { t } = useTranslation();
  const { linkVisible, isIOS, install } = useInstall();
  const [showIOSHint, setShowIOSHint] = React.useState(false);

  if (!linkVisible) return null;

  return (
    <div className="md:hidden mt-8 pt-6 border-t border-border text-center">
      {isIOS ? (
        <>
          <button
            onClick={() => setShowIOSHint(h => !h)}
            className="text-xs text-muted-foreground hover:text-primary transition-colors inline-flex items-center gap-1.5"
          >
            <i className="fas fa-mobile-alt" />
            {t('Add app to home screen')}
          </button>
          {showIOSHint && (
            <p className="mt-2 text-xs text-muted-foreground">
              {t('Tap')} <i className="fas fa-share-square" /> {t('then')} <strong>{t('Add to Home Screen')}</strong>
            </p>
          )}
        </>
      ) : (
        <button
          onClick={install}
          className="text-xs text-muted-foreground hover:text-primary transition-colors inline-flex items-center gap-1.5"
        >
          <i className="fas fa-mobile-alt" />
          {t('Add app to home screen')}
        </button>
      )}
    </div>
  );
}

const EventInfoWithI18n = withTranslation()(EventInfo);

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
          render={(props) => <EventInfoWithI18n {...props} event={event} user={this.props.user} isConfirmedGuest={this.state.isConfirmedGuest}/>}
        />
        <Route
          exact
          path={`${match.path}/dashboard`}
          render={(props) => <EventDashboard {...props} event={event} user={this.props.user}/>}
        />
        <Route
          exact
          path={`${match.path}/resourceLinks`}
          render={(props) => <ResourceLinksAdmin {...props} event={event} user={this.props.user} organisation={this.props.organisation}/>}
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
