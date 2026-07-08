import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import { programmeService } from '../../services/eventApp/programme.service';
import { eventLocalDateKey, formatTimezoneLabel } from '../../utils/datetime';
import ProgrammeSchedule from '../../components/ProgrammeSchedule';

function DayButton(props) {
  return React.createElement('button', {
    onClick: props.onClick,
    className: 'px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap flex-shrink-0 transition-colors ' +
      (props.active
        ? 'bg-primary text-white'
        : 'bg-muted text-muted-foreground hover:bg-muted/80')
  }, props.label);
}

function FilterChip(props) {
  return React.createElement('button', {
    onClick: props.onClick,
    className: 'px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap flex-shrink-0 transition-colors border ' +
      (props.active
        ? 'bg-primary/10 border-primary text-primary'
        : 'bg-white border-border text-muted-foreground hover:bg-muted/50')
  }, props.label);
}

class EventAppProgramme extends Component {
  constructor(props) {
    super(props);
    this.state = {
      sessions: [],
      sessionTypes: [],
      tracks: [],
      isLoading: true,
      error: null,
      selectedDay: null,
      selectedTypeId: null,
      selectedTrackIds: {},
      searchQuery: '',
    };
    this.handleSearch = this.handleSearch.bind(this);
  }

  componentDidMount() {
    var event = this.props.event;
    if (!event) return;
    var self = this;
    Promise.all([
      programmeService.listSessions(event.id),
      programmeService.listSessionTypes(event.id),
      programmeService.listTracks(event.id),
    ]).then(function(results) {
      var sessions = results[0].data || [];
      var sessionTypes = results[1].data || [];
      var tracks = results[2].data || [];
      var timezone = event.timezone || 'UTC';
      // Build sorted unique days
      var daySet = {};
      sessions.forEach(function(s) {
        if (s.start_time) {
          var key = eventLocalDateKey(s.start_time, timezone);
          daySet[key] = true;
        }
      });
      var days = Object.keys(daySet).sort();
      self.setState({
        sessions: sessions,
        sessionTypes: sessionTypes,
        tracks: tracks,
        days: days,
        selectedDay: days.length > 0 ? days[0] : null,
        isLoading: false,
      });
    }).catch(function(err) {
      self.setState({ isLoading: false, error: String(err) });
    });
  }

  handleSearch(e) {
    this.setState({ searchQuery: e.target.value });
  }

  getFilteredSessions() {
    var self = this;
    var state = self.state;
    var event = self.props.event;
    var timezone = (event && event.timezone) || 'UTC';
    var query = state.searchQuery.trim().toLowerCase();

    return state.sessions.filter(function(s) {
      if (state.selectedDay) {
        var dayKey = eventLocalDateKey(s.start_time, timezone);
        if (dayKey !== state.selectedDay) return false;
      }
      if (state.selectedTypeId !== null) {
        if (!s.session_type || s.session_type.id !== state.selectedTypeId) return false;
      }
      var activeTrackIds = Object.keys(state.selectedTrackIds).filter(function(k) {
        return state.selectedTrackIds[k];
      });
      if (activeTrackIds.length > 0) {
        var sessionTrackIds = (s.tracks || []).map(function(tr) { return String(tr.id); });
        var hasTrack = activeTrackIds.some(function(id) { return sessionTrackIds.indexOf(id) !== -1; });
        if (!hasTrack) return false;
      }
      if (query) {
        var titleMatch = (s.title || '').toLowerCase().indexOf(query) !== -1;
        var speakerMatch = (s.speakers || []).some(function(sp) {
          return sp.name.toLowerCase().indexOf(query) !== -1;
        });
        if (!titleMatch && !speakerMatch) return false;
      }
      return true;
    });
  }

  render() {
    var t = this.props.t;
    var event = this.props.event;
    var timezone = (event && event.timezone) || 'UTC';
    var state = this.state;
    var self = this;
    var filteredSessions = this.getFilteredSessions();

    if (state.isLoading) {
      return React.createElement('div', { className: 'w-full pt-6 text-center text-muted-foreground' },
        t('Loading')
      );
    }

    if (state.error) {
      return React.createElement('div', { className: 'w-full pt-6 text-center text-destructive' },
        state.error
      );
    }

    return React.createElement('div', { className: 'w-full' },

      // Header + Search — opaque so the scrolling schedule never shows through
      React.createElement('div', { className: 'sticky top-0 z-20 bg-background pt-4 pb-3 border-b border-border/60 shadow-sm' },
        // Opaque band covering the scroll container's top padding (py-8), so the
        // schedule cannot peek through the gap above the sticky header.
        React.createElement('div', { 'aria-hidden': true, className: 'absolute inset-x-0 -top-8 h-8 bg-background pointer-events-none' }),
        React.createElement('div', { className: 'space-y-3' },
        React.createElement('div', { className: 'flex items-center justify-between gap-4' },
          React.createElement('h1', { className: 'font-heading text-2xl font-bold text-foreground' },
            t('Programme')
          )
        ),

        // Timezone notice
        React.createElement('p', { className: 'text-xs text-muted-foreground' },
          t('Times shown in') + ' ' + formatTimezoneLabel(timezone, event && event.start_date)
        ),

        // Search
        React.createElement('div', { className: 'relative' },
          React.createElement('i', { className: 'fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground', style: { fontSize: 14 } }),
          React.createElement('input', {
            type: 'text',
            placeholder: t('Search sessions or speakers...'),
            value: state.searchQuery,
            onChange: self.handleSearch,
            className: 'w-full pl-9 pr-4 py-2 text-sm border border-border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary/30'
          })
        ),

        // Day chips
        state.days && state.days.length > 0 && React.createElement('div', {
          className: 'flex gap-2 overflow-x-auto pb-1 hide-scrollbar'
        },
          state.days.map(function(day, i) {
            var label = t('Day') + ' ' + (i + 1) + ' – ' + day;
            return React.createElement(DayButton, {
              key: day,
              label: label,
              active: state.selectedDay === day,
              onClick: function() { self.setState({ selectedDay: day }); }
            });
          })
        ),

        // Session type filter
        state.sessionTypes.length > 0 && React.createElement('div', {
          className: 'flex gap-2 overflow-x-auto pb-1 hide-scrollbar'
        },
          React.createElement(FilterChip, {
            label: t('All Types'),
            active: state.selectedTypeId === null,
            onClick: function() { self.setState({ selectedTypeId: null }); }
          }),
          state.sessionTypes.map(function(st) {
            return React.createElement(FilterChip, {
              key: st.id,
              label: st.name,
              active: state.selectedTypeId === st.id,
              onClick: function() {
                self.setState({ selectedTypeId: state.selectedTypeId === st.id ? null : st.id });
              }
            });
          })
        ),

        // Track filter
        state.tracks.length > 0 && React.createElement('div', {
          className: 'flex gap-2 overflow-x-auto pb-1 hide-scrollbar'
        },
          state.tracks.map(function(tr) {
            return React.createElement(FilterChip, {
              key: tr.id,
              label: tr.name,
              active: !!(state.selectedTrackIds[tr.id]),
              onClick: function() {
                var next = Object.assign({}, state.selectedTrackIds);
                next[tr.id] = !next[tr.id];
                self.setState({ selectedTrackIds: next });
              }
            });
          })
        )
        )
      ),

      // Schedule — grouped by start time, parallel sessions scroll horizontally
      React.createElement('div', { className: 'pt-4' },
        filteredSessions.length === 0
          ? React.createElement('p', { className: 'text-center text-muted-foreground py-12' },
              t('No sessions found.')
            )
          : React.createElement(ProgrammeSchedule, {
              sessions: filteredSessions,
              timezone: timezone,
              t: t,
              eventKey: event && event.key,
              linkSpeakers: true
            })
      )
    );
  }
}

export default withTranslation()(EventAppProgramme);
