import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import { programmeService } from '../../services/eventApp/programme.service';
import {
  eventLocalDateKey,
  eventLocalToUtcIso,
  formatTimeInEventTz,
  utcToEventLocalDate,
  utcToEventLocalTime,
} from '../../utils/datetime';
import { translationService } from '../../services/translation/translation.service';
import ScheduleGrid from '../../components/ScheduleGrid';

// ── Helpers ──────────────────────────────────────────────────────────────────

function getEventDays(event) {
  if (!event || !event.start_date || !event.end_date) return [];
  var start = new Date(event.start_date);
  var end = new Date(event.end_date);
  var days = [];
  var cur = new Date(start.getFullYear(), start.getMonth(), start.getDate());
  var endDay = new Date(end.getFullYear(), end.getMonth(), end.getDate());
  while (cur <= endDay) {
    var y = cur.getFullYear();
    var m = String(cur.getMonth() + 1).padStart(2, '0');
    var d = String(cur.getDate()).padStart(2, '0');
    days.push(y + '-' + m + '-' + d);
    cur.setDate(cur.getDate() + 1);
  }
  return days;
}

function blankSessionForm(eventId, date) {
  return {
    event_id: eventId,
    date: date || '',
    start_time: '09:00',
    end_time: '10:00',
    venue: '',
    session_type_id: '',
    speaker_ids: [],
    track_tag_ids: [],
    title_en: '',
    title_fr: '',
    desc_en: '',
    desc_fr: '',
  };
}

function formatDayLabel(dateStr, t) {
  if (!dateStr) return '';
  var d = new Date(dateStr + 'T12:00:00Z');
  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' });
}

// ── Session Form Modal ────────────────────────────────────────────────────────

class SessionFormModal extends Component {
  constructor(props) {
    super(props);
    this.state = {
      form: props.initialForm || blankSessionForm(props.eventId, props.selectedDay),
      newSpeakerName: '',
      newSpeakerEmail: '',
      newTypeName: '',
      newTrackName: '',
      isTranslating: false,
      isSaving: false,
      error: null,
    };
    this.handleChange = this.handleChange.bind(this);
    this.handleSpeakerToggle = this.handleSpeakerToggle.bind(this);
    this.handleTrackToggle = this.handleTrackToggle.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleAutoTranslate = this.handleAutoTranslate.bind(this);
    this.handleAddSpeaker = this.handleAddSpeaker.bind(this);
    this.handleAddType = this.handleAddType.bind(this);
    this.handleAddTrack = this.handleAddTrack.bind(this);
  }

  handleChange(e) {
    var name = e.target.name;
    var value = e.target.value;
    this.setState(function(prev) {
      return { form: Object.assign({}, prev.form, { [name]: value }) };
    });
  }

  handleSpeakerToggle(speakerId) {
    this.setState(function(prev) {
      var ids = prev.form.speaker_ids.slice();
      var idx = ids.indexOf(speakerId);
      if (idx === -1) {
        ids.push(speakerId);
      } else {
        ids.splice(idx, 1);
      }
      return { form: Object.assign({}, prev.form, { speaker_ids: ids }) };
    });
  }

  handleTrackToggle(tagId) {
    this.setState(function(prev) {
      var ids = prev.form.track_tag_ids.slice();
      var idx = ids.indexOf(tagId);
      if (idx === -1) {
        ids.push(tagId);
      } else {
        ids.splice(idx, 1);
      }
      return { form: Object.assign({}, prev.form, { track_tag_ids: ids }) };
    });
  }

  handleAutoTranslate() {
    var self = this;
    var titleEn = self.state.form.title_en;
    var descEn = self.state.form.desc_en;
    if (!titleEn && !descEn) return;
    self.setState({ isTranslating: true });
    var promises = [];
    if (titleEn) {
      promises.push(translationService.translateText(titleEn, 'en', ['fr']));
    } else {
      promises.push(Promise.resolve({ translations: null }));
    }
    if (descEn) {
      promises.push(translationService.translateText(descEn, 'en', ['fr']));
    } else {
      promises.push(Promise.resolve({ translations: null }));
    }
    Promise.all(promises).then(function(results) {
      var titleFr = (results[0].translations && results[0].translations.fr) || self.state.form.title_fr;
      var descFr = (results[1].translations && results[1].translations.fr) || self.state.form.desc_fr;
      self.setState(function(prev) {
        return {
          isTranslating: false,
          form: Object.assign({}, prev.form, { title_fr: titleFr, desc_fr: descFr })
        };
      });
    }).catch(function() {
      self.setState({ isTranslating: false });
    });
  }

  handleAddSpeaker() {
    var self = this;
    var name = self.state.newSpeakerName.trim();
    var email = self.state.newSpeakerEmail.trim();
    if (!name) return;
    programmeService.createSpeaker({
      event_id: self.props.eventId,
      name: name,
      email: email || undefined,
    }).then(function(result) {
      if (result.data) {
        self.props.onSpeakerCreated(result.data);
        self.setState(function(prev) {
          return {
            newSpeakerName: '',
            newSpeakerEmail: '',
            form: Object.assign({}, prev.form, {
              speaker_ids: prev.form.speaker_ids.concat([result.data.id])
            })
          };
        });
      }
    });
  }

  handleAddType() {
    var self = this;
    var name = self.state.newTypeName.trim();
    if (!name) return;
    programmeService.addSessionType({
      event_id: self.props.eventId,
      name: { en: name },
    }).then(function(result) {
      if (result.data) {
        self.props.onSessionTypeCreated(result.data);
        self.setState(function(prev) {
          return {
            newTypeName: '',
            form: Object.assign({}, prev.form, { session_type_id: String(result.data.id) })
          };
        });
      }
    });
  }

  handleAddTrack() {
    var self = this;
    var name = self.state.newTrackName.trim();
    if (!name) return;
    programmeService.addTrack({
      event_id: self.props.eventId,
      name: { en: name },
    }).then(function(result) {
      if (result.data) {
        self.props.onTrackCreated(result.data);
        self.setState(function(prev) {
          return {
            newTrackName: '',
            form: Object.assign({}, prev.form, {
              track_tag_ids: prev.form.track_tag_ids.concat([result.data.id])
            })
          };
        });
      }
    });
  }

  handleSubmit(e) {
    e.preventDefault();
    var self = this;
    var form = self.state.form;
    var timezone = self.props.timezone;

    if (!form.title_en.trim()) {
      self.setState({ error: self.props.t('Session title (EN) is required.') });
      return;
    }
    if (!form.date || !form.start_time || !form.end_time) {
      self.setState({ error: self.props.t('Date, start time and end time are required.') });
      return;
    }

    var startUtc = eventLocalToUtcIso(form.date, form.start_time, timezone);
    var endUtc = eventLocalToUtcIso(form.date, form.end_time, timezone);

    var translations = [{ language: 'en', title: form.title_en.trim(), description: form.desc_en }];
    if (form.title_fr.trim()) {
      translations.push({ language: 'fr', title: form.title_fr.trim(), description: form.desc_fr });
    }

    var payload = {
      event_id: form.event_id,
      translations: translations,
      session_type_id: form.session_type_id ? Number(form.session_type_id) : null,
      venue: form.venue,
      start_time: startUtc,
      end_time: endUtc,
      speaker_ids: form.speaker_ids,
      track_tag_ids: form.track_tag_ids,
    };

    self.setState({ isSaving: true, error: null });

    var promise = self.props.sessionId
      ? programmeService.updateSession(self.props.sessionId, payload)
      : programmeService.createSession(payload);

    promise.then(function(result) {
      if (result.error) {
        self.setState({ isSaving: false, error: result.error });
      } else {
        self.setState({ isSaving: false });
        self.props.onSaved(result.data);
      }
    });
  }

  render() {
    var t = this.props.t;
    var form = this.state.form;
    var speakers = this.props.speakers || [];
    var sessionTypes = this.props.sessionTypes || [];
    var tracks = this.props.tracks || [];
    var self = this;

    return React.createElement('div', {
      className: 'fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40',
      onClick: function(e) { if (e.target === e.currentTarget) self.props.onClose(); }
    },
      React.createElement('div', {
        className: 'bg-white w-full sm:max-w-lg sm:rounded-2xl rounded-t-2xl max-h-[90vh] flex flex-col shadow-2xl'
      },
        // Header
        React.createElement('div', { className: 'flex items-center justify-between px-5 py-4 border-b border-border flex-shrink-0' },
          React.createElement('h2', { className: 'font-heading text-lg font-bold text-foreground' },
            self.props.sessionId ? t('Edit Session') : t('New Session')
          ),
          React.createElement('button', {
            onClick: self.props.onClose,
            className: 'text-muted-foreground hover:text-foreground p-1'
          },
            React.createElement('svg', { xmlns: 'http://www.w3.org/2000/svg', width: '20', height: '20', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: '2', strokeLinecap: 'round', strokeLinejoin: 'round' },
              React.createElement('line', { x1: '18', y1: '6', x2: '6', y2: '18' }),
              React.createElement('line', { x1: '6', y1: '6', x2: '18', y2: '18' })
            )
          )
        ),

        // Body — scrollable
        React.createElement('form', {
          onSubmit: self.handleSubmit,
          className: 'overflow-y-auto flex-1 px-5 py-4 space-y-4'
        },
          self.state.error && React.createElement('p', { className: 'text-sm text-destructive bg-destructive/10 rounded p-2' },
            self.state.error
          ),

          // Title EN
          React.createElement('div', null,
            React.createElement('label', { className: 'block text-xs font-semibold text-muted-foreground mb-1 uppercase tracking-wider' },
              t('Title (English)') + ' *'
            ),
            React.createElement('input', {
              type: 'text',
              name: 'title_en',
              value: form.title_en,
              onChange: self.handleChange,
              className: 'w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30',
              placeholder: t('Session title in English')
            })
          ),

          // Desc EN
          React.createElement('div', null,
            React.createElement('label', { className: 'block text-xs font-semibold text-muted-foreground mb-1 uppercase tracking-wider' },
              t('Description (English)')
            ),
            React.createElement('textarea', {
              name: 'desc_en',
              value: form.desc_en,
              onChange: self.handleChange,
              rows: 3,
              className: 'w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none',
              placeholder: t('Optional description or abstract')
            })
          ),

          // Auto-translate button
          React.createElement('button', {
            type: 'button',
            onClick: self.handleAutoTranslate,
            disabled: self.state.isTranslating,
            className: 'flex items-center gap-1 text-xs text-primary border border-primary/30 rounded-lg px-3 py-1.5 hover:bg-primary/5 transition-colors'
          },
            React.createElement('svg', { xmlns: 'http://www.w3.org/2000/svg', width: '14', height: '14', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: '2', strokeLinecap: 'round', strokeLinejoin: 'round' },
              React.createElement('path', { d: 'M5 8l6 6' }),
              React.createElement('path', { d: 'm4 14 6-6 2-3' }),
              React.createElement('path', { d: 'M2 5h12' }),
              React.createElement('path', { d: 'M7 2h1' }),
              React.createElement('path', { d: 'm22 22-5-10-5 10' }),
              React.createElement('path', { d: 'M14 18h6' })
            ),
            self.state.isTranslating ? t('Translating...') : t('Auto-translate to French')
          ),

          // Title FR
          React.createElement('div', null,
            React.createElement('label', { className: 'block text-xs font-semibold text-muted-foreground mb-1 uppercase tracking-wider' },
              t('Title (French)')
            ),
            React.createElement('input', {
              type: 'text',
              name: 'title_fr',
              value: form.title_fr,
              onChange: self.handleChange,
              className: 'w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30',
              placeholder: t('Session title in French (optional)')
            })
          ),

          // Desc FR
          React.createElement('div', null,
            React.createElement('label', { className: 'block text-xs font-semibold text-muted-foreground mb-1 uppercase tracking-wider' },
              t('Description (French)')
            ),
            React.createElement('textarea', {
              name: 'desc_fr',
              value: form.desc_fr,
              onChange: self.handleChange,
              rows: 2,
              className: 'w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none',
              placeholder: t('Optional')
            })
          ),

          // Date + Times
          React.createElement('div', { className: 'grid grid-cols-3 gap-3' },
            React.createElement('div', null,
              React.createElement('label', { className: 'block text-xs font-semibold text-muted-foreground mb-1 uppercase tracking-wider' },
                t('Date') + ' *'
              ),
              React.createElement('input', {
                type: 'date',
                name: 'date',
                value: form.date,
                onChange: self.handleChange,
                className: 'w-full border border-border rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30'
              })
            ),
            React.createElement('div', null,
              React.createElement('label', { className: 'block text-xs font-semibold text-muted-foreground mb-1 uppercase tracking-wider' },
                t('Start')
              ),
              React.createElement('input', {
                type: 'time',
                step: 300,
                name: 'start_time',
                value: form.start_time,
                onChange: self.handleChange,
                className: 'w-full border border-border rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30'
              })
            ),
            React.createElement('div', null,
              React.createElement('label', { className: 'block text-xs font-semibold text-muted-foreground mb-1 uppercase tracking-wider' },
                t('End')
              ),
              React.createElement('input', {
                type: 'time',
                step: 300,
                name: 'end_time',
                value: form.end_time,
                onChange: self.handleChange,
                className: 'w-full border border-border rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30'
              })
            )
          ),

          // Venue
          React.createElement('div', null,
            React.createElement('label', { className: 'block text-xs font-semibold text-muted-foreground mb-1 uppercase tracking-wider' },
              t('Venue')
            ),
            React.createElement('input', {
              type: 'text',
              name: 'venue',
              value: form.venue,
              onChange: self.handleChange,
              className: 'w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30',
              placeholder: t('Room / venue name')
            })
          ),

          // Session type
          React.createElement('div', null,
            React.createElement('label', { className: 'block text-xs font-semibold text-muted-foreground mb-1 uppercase tracking-wider' },
              t('Session Type')
            ),
            React.createElement('div', { className: 'flex gap-2' },
              React.createElement('select', {
                name: 'session_type_id',
                value: form.session_type_id,
                onChange: self.handleChange,
                className: 'flex-1 border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 bg-white'
              },
                React.createElement('option', { value: '' }, t('— None —')),
                sessionTypes.map(function(st) {
                  return React.createElement('option', { key: st.id, value: String(st.id) }, st.name);
                })
              ),
              React.createElement('input', {
                type: 'text',
                placeholder: t('+ New type'),
                value: self.state.newTypeName,
                onChange: function(e) { self.setState({ newTypeName: e.target.value }); },
                onKeyDown: function(e) { if (e.key === 'Enter') { e.preventDefault(); self.handleAddType(); } },
                className: 'w-28 border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30'
              }),
              React.createElement('button', {
                type: 'button',
                onClick: self.handleAddType,
                className: 'px-3 py-2 bg-muted rounded-lg text-sm hover:bg-muted/80 transition-colors'
              }, t('Add'))
            )
          ),

          // Tracks
          React.createElement('div', null,
            React.createElement('label', { className: 'block text-xs font-semibold text-muted-foreground mb-1 uppercase tracking-wider' },
              t('Tracks')
            ),
            React.createElement('div', { className: 'flex flex-wrap gap-2 mb-2' },
              tracks.map(function(tr) {
                var selected = form.track_tag_ids.indexOf(tr.id) !== -1;
                return React.createElement('button', {
                  key: tr.id,
                  type: 'button',
                  onClick: function() { self.handleTrackToggle(tr.id); },
                  className: 'px-3 py-1 rounded-full text-xs border transition-colors ' +
                    (selected
                      ? 'bg-primary text-white border-primary'
                      : 'bg-white text-muted-foreground border-border hover:bg-muted/50')
                }, tr.name);
              })
            ),
            React.createElement('div', { className: 'flex gap-2' },
              React.createElement('input', {
                type: 'text',
                placeholder: t('+ New track'),
                value: self.state.newTrackName,
                onChange: function(e) { self.setState({ newTrackName: e.target.value }); },
                onKeyDown: function(e) { if (e.key === 'Enter') { e.preventDefault(); self.handleAddTrack(); } },
                className: 'flex-1 border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30'
              }),
              React.createElement('button', {
                type: 'button',
                onClick: self.handleAddTrack,
                className: 'px-3 py-2 bg-muted rounded-lg text-sm hover:bg-muted/80 transition-colors'
              }, t('Add'))
            )
          ),

          // Speakers
          React.createElement('div', null,
            React.createElement('label', { className: 'block text-xs font-semibold text-muted-foreground mb-1 uppercase tracking-wider' },
              t('Speakers')
            ),
            React.createElement('div', { className: 'space-y-1 mb-2' },
              speakers.map(function(spk) {
                var selected = form.speaker_ids.indexOf(spk.id) !== -1;
                return React.createElement('div', {
                  key: spk.id,
                  onClick: function() { self.handleSpeakerToggle(spk.id); },
                  className: 'flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ' +
                    (selected ? 'bg-primary/10 border border-primary/20' : 'hover:bg-muted/50 border border-transparent')
                },
                  React.createElement('div', {
                    className: 'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 ' +
                      (selected ? 'bg-primary border-primary' : 'border-border')
                  },
                    selected && React.createElement('svg', { xmlns: 'http://www.w3.org/2000/svg', width: '12', height: '12', viewBox: '0 0 24 24', fill: 'none', stroke: 'white', strokeWidth: '3', strokeLinecap: 'round', strokeLinejoin: 'round' },
                      React.createElement('polyline', { points: '20 6 9 17 4 12' })
                    )
                  ),
                  spk.photo_url && React.createElement('img', {
                    src: spk.photo_url,
                    alt: spk.name,
                    className: 'w-7 h-7 rounded-full object-cover'
                  }),
                  React.createElement('div', { className: 'flex-1 min-w-0' },
                    React.createElement('span', { className: 'text-sm font-medium text-foreground' }, spk.name),
                    spk.linked_user_id && React.createElement('span', {
                      className: 'ml-2 text-xs text-primary bg-primary/10 rounded px-1'
                    }, t('Member'))
                  )
                );
              })
            ),
            // Add new speaker inline
            React.createElement('div', { className: 'border border-dashed border-border rounded-lg p-3 space-y-2' },
              React.createElement('p', { className: 'text-xs text-muted-foreground font-medium' }, t('Add new speaker')),
              React.createElement('div', { className: 'flex gap-2' },
                React.createElement('input', {
                  type: 'text',
                  placeholder: t('Name'),
                  value: self.state.newSpeakerName,
                  onChange: function(e) { self.setState({ newSpeakerName: e.target.value }); },
                  className: 'flex-1 border border-border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary/30'
                }),
                React.createElement('input', {
                  type: 'email',
                  placeholder: t('Email (optional)'),
                  value: self.state.newSpeakerEmail,
                  onChange: function(e) { self.setState({ newSpeakerEmail: e.target.value }); },
                  className: 'flex-1 border border-border rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary/30'
                }),
                React.createElement('button', {
                  type: 'button',
                  onClick: self.handleAddSpeaker,
                  className: 'px-3 py-1.5 bg-muted rounded text-sm hover:bg-muted/80 transition-colors'
                }, t('Add'))
              )
            )
          ),

          // Submit row
          React.createElement('div', { className: 'flex gap-3 pt-2' },
            React.createElement('button', {
              type: 'button',
              onClick: self.props.onClose,
              className: 'flex-1 border border-border rounded-lg py-2 text-sm font-medium text-muted-foreground hover:bg-muted/50 transition-colors'
            }, t('Cancel')),
            React.createElement('button', {
              type: 'submit',
              disabled: self.state.isSaving,
              className: 'flex-1 bg-primary text-white rounded-lg py-2 text-sm font-semibold hover:bg-primary/90 transition-colors disabled:opacity-60'
            }, self.state.isSaving ? t('Saving...') : t('Save Session'))
          )
        )
      )
    );
  }
}

// ── Session card in the editor list ──────────────────────────────────────────

function EditorSessionCard(props) {
  var session = props.session;
  var timezone = props.timezone;
  var t = props.t;

  var startTime = session.start_time
    ? new Intl.DateTimeFormat('en-GB', { timeZone: timezone, hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(session.start_time))
    : '';
  var endTime = session.end_time
    ? new Intl.DateTimeFormat('en-GB', { timeZone: timezone, hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(session.end_time))
    : '';

  return React.createElement('div', {
    className: 'bg-white rounded-xl border border-border shadow-sm overflow-hidden h-full flex flex-col'
  },
    React.createElement('div', { className: 'w-full h-1 flex-shrink-0 bg-primary' }),
    React.createElement('div', { className: 'p-2.5 flex-1 min-w-0 overflow-hidden flex flex-col gap-1' },
      React.createElement('div', { className: 'flex items-start justify-between gap-1' },
        React.createElement('div', { className: 'flex-1 min-w-0 overflow-hidden' },
          React.createElement('div', { className: 'flex items-center gap-1.5 flex-wrap mb-0.5' },
            React.createElement('span', { className: 'text-xs font-semibold text-primary whitespace-nowrap' },
              startTime + ' – ' + endTime
            ),
            session.session_type && React.createElement('span', {
              className: 'bg-primary/10 text-primary text-xs px-1.5 py-0.5 rounded-full font-medium'
            }, session.session_type.name),
            session.venue && React.createElement('span', {
              className: 'text-xs text-muted-foreground flex items-center gap-0.5'
            },
              React.createElement('svg', { xmlns: 'http://www.w3.org/2000/svg', width: '11', height: '11', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: '2', strokeLinecap: 'round', strokeLinejoin: 'round' },
                React.createElement('path', { d: 'M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z' }),
                React.createElement('circle', { cx: '12', cy: '10', r: '3' })
              ),
              session.venue
            )
          ),
          React.createElement('h3', { className: 'font-medium text-sm text-foreground leading-snug' },
            session.title || t('Untitled Session')
          ),
          (session.speakers || []).length > 0 && React.createElement('p', {
            className: 'text-xs text-muted-foreground truncate'
          },
            session.speakers.map(function(s) { return s.name; }).join(', ')
          )
        ),
        React.createElement('div', { className: 'flex gap-1 flex-shrink-0' },
            React.createElement('button', {
              onClick: function() { props.onEdit(session); },
              className: 'p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/5 rounded-lg transition-colors',
              title: t('Edit')
            },
              React.createElement('svg', { xmlns: 'http://www.w3.org/2000/svg', width: '16', height: '16', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: '2', strokeLinecap: 'round', strokeLinejoin: 'round' },
                React.createElement('path', { d: 'M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7' }),
                React.createElement('path', { d: 'M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z' })
              )
            ),
            React.createElement('button', {
              onClick: function() { props.onDelete(session); },
              className: 'p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/5 rounded-lg transition-colors',
              title: t('Delete')
            },
              React.createElement('svg', { xmlns: 'http://www.w3.org/2000/svg', width: '16', height: '16', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: '2', strokeLinecap: 'round', strokeLinejoin: 'round' },
                React.createElement('polyline', { points: '3 6 5 6 21 6' }),
                React.createElement('path', { d: 'M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6' }),
                React.createElement('path', { d: 'M10 11v6' }),
                React.createElement('path', { d: 'M14 11v6' }),
                React.createElement('path', { d: 'M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2' })
              )
            )
          )
        )
      )
  );
}

// ── Main ProgrammeEditor component ───────────────────────────────────────────

class ProgrammeEditor extends Component {
  constructor(props) {
    super(props);
    this.state = {
      sessions: [],
      speakers: [],
      sessionTypes: [],
      tracks: [],
      isLoading: true,
      error: null,
      selectedDay: null,
      showModal: false,
      editingSession: null,
    };
    this.handleNewSession = this.handleNewSession.bind(this);
    this.handleEdit = this.handleEdit.bind(this);
    this.handleDelete = this.handleDelete.bind(this);
    this.handleSaved = this.handleSaved.bind(this);
    this.handleCloseModal = this.handleCloseModal.bind(this);
  }

  componentDidMount() {
    var event = this.props.event;
    if (!event) return;
    var self = this;
    Promise.all([
      programmeService.listSessions(event.id),
      programmeService.listSpeakers(event.id),
      programmeService.listSessionTypes(event.id),
      programmeService.listTracks(event.id),
    ]).then(function(results) {
      var days = getEventDays(event);
      self.setState({
        sessions: results[0].data || [],
        speakers: results[1].data || [],
        sessionTypes: results[2].data || [],
        tracks: results[3].data || [],
        days: days,
        selectedDay: days.length > 0 ? days[0] : null,
        isLoading: false,
      });
    }).catch(function(err) {
      self.setState({ isLoading: false, error: String(err) });
    });
  }

  handleNewSession() {
    this.setState({ showModal: true, editingSession: null });
  }

  handleEdit(session) {
    var event = this.props.event;
    var timezone = (event && event.timezone) || 'UTC';
    var enTrans = (session.translations || []).find(function(t) { return t.language === 'en'; }) || {};
    var frTrans = (session.translations || []).find(function(t) { return t.language === 'fr'; }) || {};

    var initialForm = {
      event_id: session.event_id,
      date: utcToEventLocalDate(session.start_time, timezone),
      start_time: utcToEventLocalTime(session.start_time, timezone),
      end_time: utcToEventLocalTime(session.end_time, timezone),
      venue: session.venue || '',
      session_type_id: session.session_type_id ? String(session.session_type_id) : '',
      speaker_ids: (session.speakers || []).map(function(s) { return s.id; }),
      track_tag_ids: (session.tracks || []).map(function(tr) { return tr.id; }),
      title_en: enTrans.title || '',
      title_fr: frTrans.title || '',
      desc_en: enTrans.description || '',
      desc_fr: frTrans.description || '',
    };
    this.setState({ showModal: true, editingSession: session, initialForm: initialForm });
  }

  handleDelete(session) {
    var t = this.props.t;
    if (!window.confirm(t('Delete this session? This cannot be undone.'))) return;
    var self = this;
    programmeService.deleteSession(session.id).then(function(result) {
      if (result.error) {
        self.setState({ error: result.error });
      } else {
        self.setState(function(prev) {
          return {
            sessions: prev.sessions.filter(function(s) { return s.id !== session.id; })
          };
        });
      }
    });
  }

  handleSaved(savedSession) {
    var self = this;
    self.setState(function(prev) {
      var existing = prev.sessions.findIndex(function(s) { return s.id === savedSession.id; });
      var updated = prev.sessions.slice();
      if (existing !== -1) {
        updated[existing] = savedSession;
      } else {
        updated.push(savedSession);
      }
      updated.sort(function(a, b) {
        return (a.start_time || '') < (b.start_time || '') ? -1 : 1;
      });
      return { sessions: updated, showModal: false, editingSession: null };
    });
  }

  handleCloseModal() {
    this.setState({ showModal: false, editingSession: null, initialForm: null });
  }

  getSessionsForDay(day) {
    var event = this.props.event;
    var timezone = (event && event.timezone) || 'UTC';
    return this.state.sessions.filter(function(s) {
      return s.start_time && eventLocalDateKey(s.start_time, timezone) === day;
    });
  }

  render() {
    var t = this.props.t;
    var event = this.props.event;
    var timezone = (event && event.timezone) || 'UTC';
    var state = this.state;
    var self = this;

    if (state.isLoading) {
      return React.createElement('div', { className: 'w-full pt-6 text-center text-muted-foreground' },
        t('Loading')
      );
    }

    var sessionsForDay = state.selectedDay ? self.getSessionsForDay(state.selectedDay) : [];

    return React.createElement('div', { className: 'w-full' },

      // Header
      React.createElement('div', { className: 'flex items-center justify-between mb-6' },
        React.createElement('div', null,
          React.createElement('h1', { className: 'font-heading text-2xl font-bold text-foreground' },
            t('Programme Editor')
          ),
          React.createElement('p', { className: 'text-sm text-muted-foreground mt-0.5' },
            t('All times in') + ' ' + timezone
          )
        ),
        React.createElement('button', {
          onClick: self.handleNewSession,
          className: 'flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary/90 transition-colors shadow-sm'
        },
          React.createElement('svg', { xmlns: 'http://www.w3.org/2000/svg', width: '16', height: '16', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: '2.5', strokeLinecap: 'round', strokeLinejoin: 'round' },
            React.createElement('line', { x1: '12', y1: '5', x2: '12', y2: '19' }),
            React.createElement('line', { x1: '5', y1: '12', x2: '19', y2: '12' })
          ),
          t('New Session')
        )
      ),

      state.error && React.createElement('div', { className: 'mb-4 p-3 bg-destructive/10 text-destructive text-sm rounded-lg' },
        state.error
      ),

      // Day tabs
      state.days && state.days.length > 0 && React.createElement('div', {
        className: 'flex gap-1 overflow-x-auto pb-2 mb-6 hide-scrollbar'
      },
        state.days.map(function(day, i) {
          var active = state.selectedDay === day;
          return React.createElement('button', {
            key: day,
            onClick: function() { self.setState({ selectedDay: day }); },
            className: 'px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap flex-shrink-0 transition-colors ' +
              (active ? 'bg-primary text-white shadow-sm' : 'bg-muted text-muted-foreground hover:bg-muted/80')
          },
            React.createElement('span', { className: 'block' }, t('Day') + ' ' + (i + 1)),
            React.createElement('span', { className: 'block text-xs opacity-75' }, formatDayLabel(day, t))
          );
        })
      ),

      // Sessions for selected day
      sessionsForDay.length === 0
        ? React.createElement('div', {
            className: 'text-center py-16 border-2 border-dashed border-border rounded-2xl'
          },
            React.createElement('svg', { xmlns: 'http://www.w3.org/2000/svg', width: '40', height: '40', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: '1.5', strokeLinecap: 'round', strokeLinejoin: 'round', className: 'text-muted-foreground/50 mb-3 mx-auto' },
              React.createElement('rect', { x: '3', y: '4', width: '18', height: '18', rx: '2', ry: '2' }),
              React.createElement('line', { x1: '16', y1: '2', x2: '16', y2: '6' }),
              React.createElement('line', { x1: '8', y1: '2', x2: '8', y2: '6' }),
              React.createElement('line', { x1: '3', y1: '10', x2: '21', y2: '10' })
            ),
            React.createElement('p', { className: 'text-muted-foreground text-sm mb-4' }, t('No sessions for this day yet.')),
            React.createElement('button', {
              onClick: self.handleNewSession,
              className: 'bg-primary text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary/90 transition-colors'
            }, t('Add First Session'))
          )
        : React.createElement(ScheduleGrid, {
            sessions: sessionsForDay,
            timezone: timezone,
            renderCard: function(session) {
              return React.createElement(EditorSessionCard, {
                session: session,
                timezone: timezone,
                t: t,
                onEdit: self.handleEdit,
                onDelete: self.handleDelete,
              });
            }
          }),

      // Modal
      state.showModal && React.createElement(SessionFormModal, {
        eventId: event && event.id,
        timezone: timezone,
        sessionId: state.editingSession && state.editingSession.id,
        initialForm: state.initialForm || blankSessionForm(event && event.id, state.selectedDay),
        speakers: state.speakers,
        sessionTypes: state.sessionTypes,
        tracks: state.tracks,
        selectedDay: state.selectedDay,
        t: t,
        onClose: self.handleCloseModal,
        onSaved: self.handleSaved,
        onSpeakerCreated: function(spk) {
          self.setState(function(prev) {
            return { speakers: prev.speakers.concat([spk]) };
          });
        },
        onSessionTypeCreated: function(st) {
          self.setState(function(prev) {
            return { sessionTypes: prev.sessionTypes.concat([st]) };
          });
        },
        onTrackCreated: function(tr) {
          self.setState(function(prev) {
            return { tracks: prev.tracks.concat([tr]) };
          });
        },
      })
    );
  }
}

export default withTranslation()(ProgrammeEditor);
