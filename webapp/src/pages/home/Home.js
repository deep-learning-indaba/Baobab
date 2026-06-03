import React, { Component } from 'react';
import { NavLink } from 'react-router-dom';
import { withTranslation } from 'react-i18next';
import { getImage } from '../../utils/images';
import { eventService } from '../../services/events/events.service';
import { organisationService } from '../../services/organisation/organisation.service';
import { Card, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { buttonVariants } from '../../components/ui/button';
import { cn } from '../../lib/utils';

/* ── Guest hero ─────────────────────────────────────────────── */
function GuestHero({ organisation, t }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[58vh] py-16 text-center px-4">
      {organisation && (
        <img
          src={getImage(organisation.large_logo)}
          className="h-20 w-auto object-contain mb-10"
          alt={organisation.system_name}
        />
      )}
      <h1 className="font-heading text-4xl font-bold tracking-tight text-foreground mb-3 max-w-lg">
        {t('Welcome to')} {organisation?.system_name}
      </h1>
      <p className="text-muted-foreground text-base max-w-sm mb-10 leading-relaxed">
        {t('Sign up for an account to apply for events, awards, and programmes.')}
      </p>
      <div className="flex flex-wrap gap-3 justify-center">
        <NavLink to="/createAccount" className={cn(buttonVariants({ size: 'lg' }))}>
          {t('Create Account')}
        </NavLink>
        <NavLink to="/login" className={cn(buttonVariants({ variant: 'secondary', size: 'lg' }))}>
          {t('Sign In')}
        </NavLink>
      </div>
    </div>
  );
}

/* ── Application status stepper ─────────────────────────────── */
const STEPPER_STEPS = [
  { label: 'Application Submitted', subtitle: 'Oct 12, 2023', icon: 'check' },
  { label: 'Under Review', subtitle: 'In Progress', icon: 'eye' },
  { label: 'Final Decision', subtitle: 'Est. Nov 01', icon: 'user' }
];

function getApplicationStep(event) {
  const s = event?.status;
  if (!s) return 0;
  if (s.offer_status || s.outcome_status) return 2;
  if (s.application_status === 'Submitted' && !event.is_application_open) return 1;
  return 0;
}

function StatusStepper({ event, t }) {
  const current = getApplicationStep(event);
  return (
    <div className="flex items-start w-full relative pt-2">
      {/* Background line */}
      <div className="absolute top-6 left-[15%] right-[15%] h-0.5 bg-border z-0" />
      
      {STEPPER_STEPS.map((step, i) => {
        const done = i < current;
        const active = i === current;
        
        let Icon;
        if (step.icon === 'check') {
          Icon = <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />;
        } else if (step.icon === 'eye') {
          Icon = <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z M12 15a3 3 0 100-6 3 3 0 000 6z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />;
        } else {
          Icon = <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2 M12 11a4 4 0 100-8 4 4 0 000 8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />;
        }

        return (
          <div key={step.label} className="flex-1 flex flex-col items-center gap-2 relative z-10">
            <div className={cn(
              'w-8 h-8 rounded-full flex items-center justify-center transition-all bg-surface',
              (done || active) && step.icon === 'check' ? 'bg-primary text-primary-foreground' : 
              active && step.icon === 'eye' ? 'bg-blue-50 text-blue-600 ring-4 ring-blue-50' :
              !done && !active ? 'bg-surface-high text-muted-foreground border-2 border-border' :
              'bg-surface-high text-foreground border-2 border-border'
            )}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                {Icon}
              </svg>
            </div>
            <div className="text-center">
              <span className={cn(
                'block text-sm whitespace-nowrap',
                active ? 'font-bold text-foreground' : 'font-semibold text-foreground'
              )}>
                {t(step.label)}
              </span>
              <span className="block text-xs text-muted-foreground mt-0.5">
                {t(step.subtitle)}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ── Featured active application card ───────────────────────── */
function FeaturedEventCard({ event, t }) {
  // Mock status text based on step
  const currentStep = getApplicationStep(event);
  const statusPill = currentStep === 0 ? t('Applied') : currentStep === 1 ? t('Pending Review') : t('Decision Made');

  return (
    <Card className="overflow-hidden p-6 rounded-2xl shadow-sm border border-border">
      <div className="flex flex-col sm:flex-row justify-between items-start mb-2 gap-4">
        <div>
          <CardTitle className="text-2xl font-bold text-foreground mb-1">
            {event.description}
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            {t('Your application for this event is currently ')}{statusPill.toLowerCase()}.
          </p>
        </div>
        <div className="bg-primary/10 text-primary text-xs font-semibold px-3 py-1.5 rounded-md flex items-center gap-1.5 whitespace-nowrap">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
          {statusPill}
        </div>
      </div>
      
      <div className="mt-8 mb-8">
        <StatusStepper event={event} t={t} />
      </div>

      <div className="flex justify-end gap-3 mt-4 pt-4 border-t border-border/40">
        <a href={`/${event.key}/apply`} className={cn(buttonVariants({ variant: 'secondary' }))}>
          {t('View Application')}
        </a>
        <a href={`mailto:support@baobab.network`} className={cn(buttonVariants({ variant: 'default' }))}>
          {t('Contact Support')}
        </a>
      </div>
    </Card>
  );
}

/* ── Upcoming Event Card ────────────────────────────────── */
function UpcomingEventCard({ event, t }) {
  const imageUrl = event.event_type === 'EVENT'
    ? 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&q=80'
    : 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80';

  const dateStr = event.start_date || null;

  const typeLabel = {
    EVENT: t('Event'), AWARD: t('Award'), PROGRAMME: t('Programme'),
    CALL: t('Call'), JOURNAL: t('Journal'),
  }[event.event_type] || event.event_type;

  return (
    <Card className="overflow-hidden flex flex-row rounded-2xl shadow-sm border border-border">
      <div className="w-36 sm:w-48 shrink-0 overflow-hidden">
        <img src={imageUrl} alt={event.description} className="w-full h-full object-cover" />
      </div>
      <div className="p-4 flex flex-col flex-1 min-w-0">
        <span className="inline-flex items-center self-start px-2 py-0.5 rounded-md text-xs font-medium bg-surface-high text-foreground border border-border mb-2">
          {typeLabel}
        </span>
        <h3 className="font-bold text-foreground leading-snug line-clamp-2">
          <NavLink to={`/${event.key}`} className="text-foreground hover:text-primary transition-colors">
            {event.description}
          </NavLink>
        </h3>
        {dateStr && (
          <div className="flex items-center gap-1.5 text-sm text-muted-foreground mt-auto pt-3">
            <svg className="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
            <span>{t('Starts')} {dateStr}</span>
          </div>
        )}
      </div>
    </Card>
  );
}

/* ── Activity Stats Card ────────────────────────────────────── */
function ActivityStatsCard({ allEvents, attended, t }) {
  const submitted = allEvents.filter((e) => e.status?.application_status === 'Submitted').length;
  const attendedCount = attended ? attended.length : 0;
  
  // Calculate offers/outcomes
  const offersCount = allEvents.filter((e) => e.status?.offer_status).length;

  return (
    <Card className="rounded-2xl shadow-sm border border-border">
      <div className="p-4 border-b border-border bg-surface/50">
        <h3 className="font-bold text-foreground text-sm">{t('Summary Statistics')}</h3>
      </div>
      <div className="p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            </div>
            <span className="text-sm font-medium text-foreground">{t('Applications in Progress')}</span>
          </div>
          <span className="text-lg font-bold text-foreground">{submitted}</span>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-green-50 text-green-600 flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            </div>
            <span className="text-sm font-medium text-foreground">{t('Offers Received')}</span>
          </div>
          <span className="text-lg font-bold text-foreground">{offersCount}</span>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-purple-50 text-purple-600 flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            </div>
            <span className="text-sm font-medium text-foreground">{t('Events Attended')}</span>
          </div>
          <span className="text-lg font-bold text-foreground">{attendedCount}</span>
        </div>
      </div>
    </Card>
  );
}

/* ── Main Home component ────────────────────────────────────── */
class Home extends Component {
  constructor(props) {
    super(props);
    this.state = {
      allEvents: [],
      upcomingEvents: null,
      awards: null,
      journals: null,
      calls: null,
      programmes: null,
      attended: null,
      organisation: null,
      errors: [],
      loading: true,
    };
  }

  componentDidMount() {
    if (this.props.user) {
      eventService.getEvents().then((response) => {
        if (response.error) {
          this.setState((prev) => ({ errors: [...prev.errors, response.error], loading: false }));
        }
        if (response.events) {
          const ev = response.events;
          this.setState({
            allEvents: ev,
            upcomingEvents: ev.filter((e) => e.event_type === 'EVENT' && (e.is_event_opening || e.is_event_open)),
            awards:         ev.filter((e) => e.event_type === 'AWARD' && (e.is_event_opening || e.is_event_open)),
            journals:       ev.filter((e) => e.event_type === 'JOURNAL'),
            calls:          ev.filter((e) => e.event_type === 'CALL' && (e.is_event_opening || e.is_event_open)),
            programmes:     ev.filter((e) => e.event_type === 'PROGRAMME' && (e.is_event_opening || e.is_event_open)),
            attended:       ev.filter((e) => !e.is_event_opening && e.status?.is_event_attendee),
            loading: false,
          });
        }
      });
    } else {
      this.setState({ loading: false });
    }

    if (this.props.setEvent) {
      this.props.setEvent(null, null);
    }

    organisationService.getOrganisation().then((response) => {
      if (response.error) {
        this.setState((prev) => ({ errors: [...prev.errors, response.error] }));
      }
      this.setState({ organisation: response.organisation });
    });
  }

  render() {
    const { t, user, i18n } = this.props;
    const { organisation, upcomingEvents, awards, journals, calls, programmes, attended, allEvents, errors, loading } = this.state;

    let logo = organisation?.large_logo;
    if (organisation?.name === 'AI4D Africa' && i18n?.language === 'fr') {
      logo = 'ai4d_logo_fr.png';
    }

    if (!user) {
      return (
        <GuestHero
          organisation={organisation ? { ...organisation, large_logo: logo } : null}
          t={t}
        />
      );
    }

    const firstName = user.firstname || user.first_name || '';

    const featuredEvent = allEvents.find(
      (e) => e.status?.application_status === 'Submitted'
        && !e.status?.offer_status
        && !e.status?.outcome_status
    );

    const openEvents = [
      ...(upcomingEvents || []),
      ...(awards || []),
      ...(calls || []),
      ...(programmes || []),
      ...(journals || []),
    ];

    const isEmpty = !loading && openEvents.length === 0 && (!attended || attended.length === 0);

    return (
      <div className="py-6">
        {/* Error banners */}
        {errors.map((err, i) => (
          <div key={i} className="mb-4 rounded-lg bg-error-container text-on-error-container px-4 py-3 text-sm">
            {err}
          </div>
        ))}

        {/* Dashboard 2-column grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">

          {/* Main column */}
          <div className="lg:col-span-2 space-y-8">

            {/* Welcome header */}
            <div className="text-left">
              <h1 className="font-heading text-3xl font-bold text-foreground">
                {t('Welcome back')}{firstName ? `, ${firstName}` : ''}
              </h1>
              <p className="text-sm text-muted-foreground mt-2">
                {t('Here is a summary of your recent activities and upcoming events in the Baobab network.')}
              </p>
            </div>

            {/* Featured active application with status stepper */}
            {featuredEvent && (
              <section>
                <FeaturedEventCard event={featuredEvent} t={t} />
              </section>
            )}

            {/* Open opportunities grid */}
            {openEvents.length > 0 && (
              <section>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-foreground">{t('Upcoming Events')}</h2>
                  <a href="/events" className="text-sm font-semibold text-primary flex items-center gap-1 hover:underline">
                    {t('View All')} &rarr;
                  </a>
                </div>
                <div className="space-y-4">
                  {openEvents.map((e) => (
                    <UpcomingEventCard key={e.key} event={e} t={t} />
                  ))}
                </div>
                {user.is_admin && (
                  <div className="mt-4">
                    <a href="../eventConfig" className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition-colors shadow-sm border border-transparent !text-white !bg-action hover:!bg-action-container">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                      {t('Create New Event')}
                    </a>
                  </div>
                )}
              </section>
            )}

            {/* Past events list */}
            {attended && attended.length > 0 && (
              <section>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-foreground">{t('Past Events')}</h2>
                </div>
                <Card className="p-0 overflow-hidden">
                  {attended.map((e, i) => (
                    <div
                      key={e.key}
                      className={cn(
                        'flex items-center justify-between gap-4 px-5 py-4 hover:bg-surface-low transition-colors',
                        i < attended.length - 1 && 'border-b border-border/50'
                      )}
                    >
                      <NavLink
                        to={`/${e.key}`}
                        className="text-sm font-medium text-foreground hover:text-primary transition-colors truncate"
                      >
                        {e.description}
                      </NavLink>
                      <Badge variant="secondary" className="shrink-0">{t('Attended')}</Badge>
                    </div>
                  ))}
                </Card>
              </section>
            )}

            {/* Empty state */}
            {isEmpty && (
              <div className="text-center py-20 border border-dashed border-border rounded-2xl text-muted-foreground">
                <p className="font-heading font-semibold text-foreground text-lg mb-1">
                  {t('No open opportunities right now')}
                </p>
                <p className="text-sm">{t('Check back soon for events, awards, and programmes.')}</p>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <ActivityStatsCard allEvents={allEvents} attended={attended} t={t} />
          </div>
        </div>
      </div>
    );
  }
}

export default withTranslation()(Home);
