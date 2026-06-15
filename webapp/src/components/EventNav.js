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
          return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-muted-foreground group-hover:text-primary transition-colors"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>;
        case 'Apply':
        case 'Submit':
        case 'Registration Form':
          return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-muted-foreground group-hover:text-primary transition-colors"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>;
        case 'Review':
        case 'Review Assignment':
        case 'Review Dashboard':
          return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-muted-foreground group-hover:text-primary transition-colors"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>;
        case 'Edit Event Details':
        case 'Form Configuration':
          return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-muted-foreground group-hover:text-primary transition-colors"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>;
        default:
          return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-muted-foreground group-hover:text-primary transition-colors"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>;
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
            {isProgrammeEditor(this.props.user, this.props.event) && (
              <SidebarLink to={`/${this.props.eventKey}/event-app/programme`} label={t('Programme')} />
            )}
            {isCommsOfficer(this.props.user, this.props.event) && (
              <SidebarLink to={`/${this.props.eventKey}/event-app/announcements`} label={t('Announcements')} />
            )}
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

