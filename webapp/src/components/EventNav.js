import React, { Component } from 'react';
import { NavLink } from 'react-router-dom';
import { withTranslation } from 'react-i18next';
import { isEventAdmin, isRegistrationAdmin, isRegistrationVolunteer, isEventReviewer, isProgrammeEditor, isCommsOfficer } from '../utils/user';

class EventNav extends Component {
  render() {
    const t = this.props.t;

    // Helper for rendering icons based on the link text/type
    const getIcon = (label) => {
      switch(label) {
        case 'Event Overview':
          return <i className="fas fa-th-large" style={{ fontSize: 15, width: 18, textAlign: 'center' }} />;
        case 'Apply':
        case 'Submit':
        case 'Registration Form':
          return <i className="fas fa-file-alt" style={{ fontSize: 15, width: 18, textAlign: 'center' }} />;
        case 'Review':
        case 'Review Assignment':
        case 'Review Dashboard':
          return <i className="fas fa-users" style={{ fontSize: 15, width: 18, textAlign: 'center' }} />;
        case 'Edit Event Details':
        case 'Form Configuration':
          return <i className="fas fa-cog" style={{ fontSize: 15, width: 18, textAlign: 'center' }} />;
        default:
          return <i className="fas fa-list" style={{ fontSize: 15, width: 18, textAlign: 'center' }} />;
      }
    };

    // A helper for single nav links
    const SidebarLink = ({ to, label, iconKey }) => (
      <li>
        <NavLink
          exact
          to={to}
          onClick={this.props.onClose}
          activeClassName="!bg-primary/5 !text-primary font-semibold shadow-[inset_4px_0_0_0_var(--color-primary)]"
          className="group flex items-start gap-3 px-1.5 py-2 rounded-lg text-sm font-medium text-foreground/80 hover:bg-surface-high hover:text-foreground transition-all text-left"
        >
          <div className="mt-0.5 shrink-0 text-muted-foreground group-hover:text-primary transition-colors">{getIcon(iconKey || label)}</div>
          <span className="leading-snug font-semibold">{label}</span>
        </NavLink>
      </li>
    );

    // A helper for expandable sections - notice normal capitalization, subtle styling
    const SidebarSection = ({ title, children }) => (
      <div className="mb-5">
        {title && (
          <h3 className="px-1.5 text-[0.8rem] font-bold text-foreground mb-2 tracking-wide text-left">
            {title}
          </h3>
        )}
        <ul className="space-y-0.5">
          {children}
        </ul>
      </div>
    );

    return (
      <nav className="w-full flex flex-col">
        <SidebarSection>
          <SidebarLink to={`/${this.props.eventKey}`} label={this.props.event?.name || t('Event Overview')} iconKey="Event Overview" />
        </SidebarSection>

        {this.props.user && this.props.event && (this.props.event.is_application_open || this.props.event.is_offer_open) && (
          <SidebarSection title={t('Applications')}>
            {this.props.event.is_application_open && (
              <SidebarLink to={`/${this.props.eventKey}/apply`} label={this.props.event.event_type === 'JOURNAL' ? t('Submit') : t('Apply')} />
            )}
            {this.props.event.is_offer_open && (
              <SidebarLink to={`/${this.props.eventKey}/offer`} label={t('Offer')} />
            )}
          </SidebarSection>
        )}

        {this.props.user && (
          <SidebarSection title={t('Registration')}>
            {this.props.event && this.props.event.is_registration_open && (
              <SidebarLink to={`/${this.props.eventKey}/registration`} label={t('Registration Form')} />
            )}
            <SidebarLink to={`/${this.props.eventKey}/invitationLetter`} label={t('Invitation Letter')} />
            <SidebarLink to={`/${this.props.eventKey}/indemnity`} label={t('Indemnity Form')} />
          </SidebarSection>
        )}

        {isEventAdmin(this.props.user, this.props.event) && (
          <SidebarSection title={t('Event Admin')}>
            <SidebarLink to={`/${this.props.eventKey}/eventConfig`} label={t('Edit Event Details')} />
            <SidebarLink to={`/${this.props.eventKey}/reviewAssignment`} label={t('Review Assignment')} />
            <SidebarLink to={`/${this.props.eventKey}/invitedGuests`} label={t('Invited Guests')} />
            <SidebarLink to={`/${this.props.eventKey}/responseList`} label={t('Response List')} />
            <SidebarLink to={`/${this.props.eventKey}/reviewDashboard`} label={t('Review Dashboard')} />
            <SidebarLink to={`/${this.props.eventKey}/tagConfig`} label={t('Configure Tags')} />
            <SidebarLink to={`/${this.props.eventKey}/offerAdmin`} label={t('Offers')} />
            <SidebarLink to={`/${this.props.eventKey}/invoices-admin`} label={t('Invoices')} />
            <SidebarLink to={`/${this.props.eventKey}/eventRoleAdmin`} label={t('Event Roles')} />
            <SidebarLink to={`/${this.props.eventKey}/formConfig`} label={t('Form Configuration')} />
            {isProgrammeEditor(this.props.user, this.props.event) && (
              <SidebarLink to={`/${this.props.eventKey}/programmeEditor`} label={t('Programme Editor')} />
            )}
          </SidebarSection>
        )}

        {isCommsOfficer(this.props.user, this.props.event) && this.props.event && (
          <SidebarSection title={t('Communications')}>
            <SidebarLink to={`/${this.props.eventKey}/announcementsAdmin`} label={t('Announcements Admin')} />
          </SidebarSection>
        )}

        {isEventReviewer(this.props.user, this.props.event) && this.props.event && this.props.event.is_review_open && (
          <SidebarSection title={t('Reviews')}>
            <SidebarLink to={`/${this.props.eventKey}/reviewlist`} label={t('Review')} />
            <SidebarLink to={`/${this.props.eventKey}/reviewHistory`} label={t('Review History')} />
          </SidebarSection>
        )}

        {this.props.isConfirmedGuest && this.props.event && (
          <SidebarSection title={t('Event App')}>
            <SidebarLink to={`/${this.props.eventKey}/event-app`} label={t('Home')} />
            <SidebarLink to={`/${this.props.eventKey}/app/ticket`} label={t('My Ticket')} />
            <SidebarLink to={`/${this.props.eventKey}/app/profile`} label={t('My Profile')} />
            <SidebarLink to={`/${this.props.eventKey}/app/community`} label={t('Browse attendees')} />
            <SidebarLink to={`/${this.props.eventKey}/app/scan`} label={t('Scan Badge')} />
            <SidebarLink to={`/${this.props.eventKey}/app/connections`} label={t('Connections')} />
            <SidebarLink to={`/${this.props.eventKey}/event-app/programme`} label={t('Programme')} />
            <SidebarLink to={`/${this.props.eventKey}/event-app/announcements`} label={t('Announcements')} />
          </SidebarSection>
        )}

        {(isRegistrationAdmin(this.props.user, this.props.event) || isRegistrationVolunteer(this.props.user, this.props.event)) && this.props.event && this.props.event.is_registration_open && (
          <SidebarSection title={t('Registration Admin')}>
            {isRegistrationAdmin(this.props.user, this.props.event) && (
              <SidebarLink to={`/${this.props.eventKey}/invoices-admin`} label={t('Invoices')} />
            )}
            {isRegistrationVolunteer(this.props.user, this.props.event) && (
              <SidebarLink to={`/${this.props.eventKey}/eventAttendance`} label={t('Event Attendance')} />
            )}
            {isRegistrationVolunteer(this.props.user, this.props.event) && (
              <SidebarLink to={`/${this.props.eventKey}/checkin`} label={t('Check-in Console')} />
            )}
            {isRegistrationAdmin(this.props.user, this.props.event) && (
              <SidebarLink to={`/${this.props.eventKey}/checkin/badges`} label={t('Badge Export')} />
            )}
          </SidebarSection>
        )}
      </nav>
    );
  }
}

const EventNavTranslation = withTranslation()(EventNav);
export default EventNavTranslation;

