import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import { programmeService } from '../../services/eventApp/programme.service';
import {
  eventLocalDateKey,
  eventLocalToUtcIso,
  formatTimezoneLabel,
  utcToEventLocalDate,
  utcToEventLocalTime,
} from '../../utils/datetime';
import ProgrammeSchedule from '../../components/ProgrammeSchedule';
import TranslatableFieldGroup from '../formEditor/components/TranslatableFieldGroup';

var DEFAULT_LANGUAGES = [{ code: 'en', description: 'English' }];

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
    title: {},
    desc: {},
  };
}

function formatDayLabel(dateStr, t) {
  if (!dateStr) return '';
  var d = new Date(dateStr + 'T12:00:00Z');
  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' });
}

// ── Speaker Picker (searchable multi-select dropdown with inline add/edit) ────

class SpeakerPicker extends Component {
  constructor(props) {
    super(props);
    this.state = {
      isOpen: false,
      searchQuery: '',
      editingId: null, // speaker id being edited, or 'new' for the add-speaker form
      editName: '',
      editEmail: '',
      error: null,
      isSaving: false,
    };
    this.containerRef = React.createRef();
    this.handleClickOutside = this.handleClickOutside.bind(this);
    this.toggleOpen = this.toggleOpen.bind(this);
    this.startAdd = this.startAdd.bind(this);
    this.cancelEdit = this.cancelEdit.bind(this);
    this.saveEdit = this.saveEdit.bind(this);
  }

  componentDidMount() {
    document.addEventListener('mousedown', this.handleClickOutside);
  }

  componentWillUnmount() {
    document.removeEventListener('mousedown', this.handleClickOutside);
  }

  handleClickOutside(e) {
    if (this.containerRef.current && !this.containerRef.current.contains(e.target)) {
      this.setState({ isOpen: false, editingId: null, error: null });
    }
  }

  toggleOpen() {
    this.setState(function(prev) {
      return { isOpen: !prev.isOpen, editingId: null, error: null };
    });
  }

  startEdit(spk) {
    this.setState({ editingId: spk.id, editName: spk.name, editEmail: spk.email || '', error: null });
  }

  startAdd() {
    this.setState({ editingId: 'new', editName: '', editEmail: '', error: null });
  }

  cancelEdit() {
    this.setState({ editingId: null, error: null });
  }

  isDuplicateName(name, excludeId) {
    var norm = name.trim().toLowerCase();
    return (this.props.speakers || []).some(function(spk) {
      return spk.id !== excludeId && spk.name.trim().toLowerCase() === norm;
    });
  }

  saveEdit() {
    var self = this;
    var t = self.props.t;
    var name = self.state.editName.trim();
    var email = self.state.editEmail.trim();
    if (!name) {
      self.setState({ error: t('Name is required.') });
      return;
    }
    var excludeId = self.state.editingId === 'new' ? null : self.state.editingId;
    if (self.isDuplicateName(name, excludeId)) {
      self.setState({ error: t('A speaker with that name already exists.') });
      return;
    }

    self.setState({ isSaving: true, error: null });

    if (self.state.editingId === 'new') {
      programmeService.createSpeaker({
        event_id: self.props.eventId,
        name: name,
        email: email || undefined,
      }).then(function(result) {
        if (result.error) {
          self.setState({ isSaving: false, error: result.error });
        } else {
          self.props.onSpeakerCreated(result.data);
          self.props.onToggle(result.data.id);
          self.setState({ isSaving: false, editingId: null, editName: '', editEmail: '' });
        }
      });
    } else {
      programmeService.updateSpeaker(self.state.editingId, {
        name: name,
        email: email,
      }).then(function(result) {
        if (result.error) {
          self.setState({ isSaving: false, error: result.error });
        } else {
          self.props.onSpeakerUpdated(result.data);
          self.setState({ isSaving: false, editingId: null, editName: '', editEmail: '' });
        }
      });
    }
  }

  render() {
    var t = this.props.t;
    var self = this;
    var speakers = this.props.speakers || [];
    var selectedIds = this.props.selectedIds || [];
    var state = this.state;

    var query = state.searchQuery.trim().toLowerCase();
    var filtered = query
      ? speakers.filter(function(spk) { return spk.name.toLowerCase().indexOf(query) !== -1; })
      : speakers;

    var selectedSpeakers = selectedIds.map(function(id) {
      return speakers.find(function(spk) { return spk.id === id; });
    }).filter(Boolean);

    return React.createElement('div', { className: 'relative', ref: this.containerRef },
      // Control
      React.createElement('div', {
        onClick: self.toggleOpen,
        className: 'flex items-center justify-between gap-2 border border-border rounded-lg px-3 py-2 min-h-[42px] cursor-pointer bg-white focus:outline-none focus:ring-2 focus:ring-primary/30'
      },
        React.createElement('div', { className: 'flex flex-wrap gap-1.5 flex-1' },
          selectedSpeakers.length === 0
            ? React.createElement('span', { className: 'text-sm text-muted-foreground' }, t('Select speakers...'))
            : selectedSpeakers.map(function(spk) {
                return React.createElement('span', {
                  key: spk.id,
                  className: 'flex items-center gap-1 bg-primary/10 text-primary text-xs font-medium rounded-full pl-2.5 pr-1.5 py-1'
                },
                  spk.name,
                  React.createElement('button', {
                    type: 'button',
                    onClick: function(e) { e.stopPropagation(); self.props.onToggle(spk.id); },
                    className: 'w-4 h-4 rounded-full flex items-center justify-center hover:bg-primary/20'
                  },
                    React.createElement('i', { className: 'fas fa-times', style: { fontSize: 9 } })
                  )
                );
              })
        ),
        React.createElement('i', {
          className: 'fas ' + (state.isOpen ? 'fa-chevron-up' : 'fa-chevron-down') + ' text-muted-foreground flex-shrink-0',
          style: { fontSize: 11 }
        })
      ),

      // Dropdown panel
      state.isOpen && React.createElement('div', {
        className: 'absolute z-20 mt-1 w-full bg-white border border-border rounded-lg shadow-lg flex flex-col max-h-80'
      },
        // Search
        React.createElement('div', { className: 'relative p-2 border-b border-border flex-shrink-0' },
          React.createElement('i', { className: 'fas fa-search absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground', style: { fontSize: 12 } }),
          React.createElement('input', {
            type: 'text',
            autoFocus: true,
            placeholder: t('Search speakers...'),
            value: state.searchQuery,
            onChange: function(e) { self.setState({ searchQuery: e.target.value }); },
            className: 'w-full pl-7 pr-2 py-1.5 text-sm border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-primary/30'
          })
        ),

        // List
        React.createElement('div', { className: 'overflow-y-auto flex-1 p-1' },
          filtered.length === 0 && React.createElement('p', { className: 'text-xs text-muted-foreground text-center py-3' }, t('No speakers found.')),
          filtered.map(function(spk) {
            if (state.editingId === spk.id) {
              return React.createElement('div', { key: spk.id, className: 'p-2 space-y-1.5 bg-muted/40 rounded-lg' },
                React.createElement('input', {
                  type: 'text',
                  value: state.editName,
                  placeholder: t('Name'),
                  onChange: function(e) { self.setState({ editName: e.target.value }); },
                  className: 'w-full border border-border rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-primary/30'
                }),
                React.createElement('input', {
                  type: 'email',
                  value: state.editEmail,
                  placeholder: t('Email (optional)'),
                  onChange: function(e) { self.setState({ editEmail: e.target.value }); },
                  className: 'w-full border border-border rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-primary/30'
                }),
                React.createElement('div', { className: 'flex gap-2 pt-0.5' },
                  React.createElement('button', {
                    type: 'button',
                    onClick: self.saveEdit,
                    disabled: state.isSaving,
                    className: 'flex-1 bg-primary text-white rounded py-1 text-xs font-semibold hover:bg-primary/90 disabled:opacity-60'
                  }, state.isSaving ? t('Saving...') : t('Save')),
                  React.createElement('button', {
                    type: 'button',
                    onClick: self.cancelEdit,
                    className: 'flex-1 border border-border rounded py-1 text-xs font-medium text-muted-foreground hover:bg-muted/50'
                  }, t('Cancel'))
                )
              );
            }

            var selected = selectedIds.indexOf(spk.id) !== -1;
            return React.createElement('div', {
              key: spk.id,
              onClick: function() { self.props.onToggle(spk.id); },
              className: 'flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors ' +
                (selected ? 'bg-primary/10' : 'hover:bg-muted/50')
            },
              React.createElement('div', {
                className: 'w-4 h-4 rounded border-2 flex items-center justify-center flex-shrink-0 ' +
                  (selected ? 'bg-primary border-primary' : 'border-border')
              },
                selected && React.createElement('i', { className: 'fas fa-check', style: { fontSize: 9, color: 'white' } })
              ),
              spk.photo_url && React.createElement('img', {
                src: spk.photo_url,
                alt: spk.name,
                className: 'w-6 h-6 rounded-full object-cover flex-shrink-0'
              }),
              React.createElement('span', { className: 'flex-1 min-w-0 text-sm text-foreground truncate' }, spk.name),
              spk.linked_user_id && React.createElement('span', {
                className: 'text-[10px] text-primary bg-primary/10 rounded px-1 flex-shrink-0'
              }, t('Member')),
              React.createElement('button', {
                type: 'button',
                onClick: function(e) { e.stopPropagation(); self.startEdit(spk); },
                title: t('Edit'),
                className: 'p-1 text-muted-foreground hover:text-primary flex-shrink-0'
              },
                React.createElement('i', { className: 'fas fa-pen', style: { fontSize: 11 } })
              )
            );
          })
        ),

        // Error
        state.error && React.createElement('p', { className: 'text-xs text-destructive px-2 pb-1 flex-shrink-0' }, state.error),

        // Footer: add new speaker
        React.createElement('div', { className: 'border-t border-border p-2 flex-shrink-0' },
          state.editingId === 'new'
            ? React.createElement('div', { className: 'space-y-1.5' },
                React.createElement('input', {
                  type: 'text',
                  value: state.editName,
                  placeholder: t('Name'),
                  autoFocus: true,
                  onChange: function(e) { self.setState({ editName: e.target.value }); },
                  className: 'w-full border border-border rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-primary/30'
                }),
                React.createElement('input', {
                  type: 'email',
                  value: state.editEmail,
                  placeholder: t('Email (optional)'),
                  onChange: function(e) { self.setState({ editEmail: e.target.value }); },
                  className: 'w-full border border-border rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-primary/30'
                }),
                React.createElement('div', { className: 'flex gap-2 pt-0.5' },
                  React.createElement('button', {
                    type: 'button',
                    onClick: self.saveEdit,
                    disabled: state.isSaving,
                    className: 'flex-1 bg-primary text-white rounded py-1 text-xs font-semibold hover:bg-primary/90 disabled:opacity-60'
                  }, state.isSaving ? t('Saving...') : t('Add')),
                  React.createElement('button', {
                    type: 'button',
                    onClick: self.cancelEdit,
                    className: 'flex-1 border border-border rounded py-1 text-xs font-medium text-muted-foreground hover:bg-muted/50'
                  }, t('Cancel'))
                )
              )
            : React.createElement('button', {
                type: 'button',
                onClick: self.startAdd,
                className: 'w-full flex items-center justify-center gap-1.5 text-xs text-primary font-medium py-1.5 hover:bg-primary/5 rounded-lg transition-colors'
              },
                React.createElement('i', { className: 'fas fa-plus', style: { fontSize: 10 } }),
                t('Add new speaker')
              )
        )
      )
    );
  }
}

// ── Session Form Modal ────────────────────────────────────────────────────────

class SessionFormModal extends Component {
  constructor(props) {
    super(props);
    this.state = {
      form: props.initialForm || blankSessionForm(props.eventId, props.selectedDay),
      newTypeName: '',
      newTrackName: '',
      isSaving: false,
      error: null,
    };
    this.handleChange = this.handleChange.bind(this);
    this.handleFieldChange = this.handleFieldChange.bind(this);
    this.handleSpeakerToggle = this.handleSpeakerToggle.bind(this);
    this.handleTrackToggle = this.handleTrackToggle.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleAddType = this.handleAddType.bind(this);
    this.handleAddTrack = this.handleAddTrack.bind(this);
  }

  getLanguages() {
    return this.props.languages || DEFAULT_LANGUAGES;
  }

  getPrimaryLanguage() {
    return this.getLanguages()[0].code;
  }

  handleChange(e) {
    var name = e.target.name;
    var value = e.target.value;
    this.setState(function(prev) {
      return { form: Object.assign({}, prev.form, { [name]: value }) };
    });
  }

  handleFieldChange(fieldName, lang, value) {
    this.setState(function(prev) {
      var next = Object.assign({}, prev.form[fieldName]);
      next[lang] = value;
      return { form: Object.assign({}, prev.form, { [fieldName]: next }) };
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

  handleAddType() {
    var self = this;
    var name = self.state.newTypeName.trim();
    if (!name) return;
    programmeService.addSessionType({
      event_id: self.props.eventId,
      name: { [self.getPrimaryLanguage()]: name },
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
      name: { [self.getPrimaryLanguage()]: name },
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
    var primaryLang = self.getPrimaryLanguage();

    if (!(form.title[primaryLang] || '').trim()) {
      self.setState({ error: self.props.t('Session title is required.') });
      return;
    }
    if (!form.date || !form.start_time || !form.end_time) {
      self.setState({ error: self.props.t('Date, start time and end time are required.') });
      return;
    }

    var startUtc = eventLocalToUtcIso(form.date, form.start_time, timezone);
    var endUtc = eventLocalToUtcIso(form.date, form.end_time, timezone);

    var translations = self.getLanguages()
      .map(function(lang) {
        return {
          language: lang.code,
          title: (form.title[lang.code] || '').trim(),
          description: form.desc[lang.code] || '',
        };
      })
      .filter(function(t) { return t.title; });

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
    var languages = this.getLanguages();
    var isMultiLingual = languages.length > 1;
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
            React.createElement('i', { className: 'fas fa-times', style: { fontSize: 18 } })
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

          // Title
          React.createElement(TranslatableFieldGroup, {
            key: 'title-group',
            label: isMultiLingual ? t('Title') + ' *' : t('Title'),
            fieldName: 'title',
            values: form.title,
            languages: languages,
            onChange: function(lang, value) { self.handleFieldChange('title', lang, value); },
            autoTranslateEnabled: isMultiLingual,
            placeholder: t('Session title')
          }),

          // Description
          React.createElement(TranslatableFieldGroup, {
            key: 'desc-group',
            label: t('Description'),
            fieldName: 'desc',
            values: form.desc,
            languages: languages,
            onChange: function(lang, value) { self.handleFieldChange('desc', lang, value); },
            autoTranslateEnabled: isMultiLingual,
            multiline: true,
            placeholder: t('Optional description or abstract')
          }),

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
            React.createElement(SpeakerPicker, {
              t: t,
              speakers: speakers,
              selectedIds: form.speaker_ids,
              onToggle: self.handleSpeakerToggle,
              eventId: self.props.eventId,
              onSpeakerCreated: self.props.onSpeakerCreated,
              onSpeakerUpdated: self.props.onSpeakerUpdated,
            })
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

// ── Edit / delete action buttons for a session card ───────────────────────────

function renderSessionActions(session, handlers, t) {
  return [
    React.createElement('button', {
      key: 'edit',
      onClick: function() { handlers.onEdit(session); },
      className: 'p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/5 rounded-lg transition-colors',
      title: t('Edit')
    },
      React.createElement('i', { className: 'fas fa-pen', style: { fontSize: 13 } })
    ),
    React.createElement('button', {
      key: 'delete',
      onClick: function() { handlers.onDelete(session); },
      className: 'p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/5 rounded-lg transition-colors',
      title: t('Delete')
    },
      React.createElement('i', { className: 'fas fa-trash-alt', style: { fontSize: 13 } })
    )
  ];
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

  getLanguages() {
    return (this.props.organisation && this.props.organisation.languages) || DEFAULT_LANGUAGES;
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
    var title = {};
    var desc = {};
    (session.translations || []).forEach(function(trans) {
      title[trans.language] = trans.title || '';
      desc[trans.language] = trans.description || '';
    });

    var initialForm = {
      event_id: session.event_id,
      date: utcToEventLocalDate(session.start_time, timezone),
      start_time: utcToEventLocalTime(session.start_time, timezone),
      end_time: utcToEventLocalTime(session.end_time, timezone),
      venue: session.venue || '',
      session_type_id: session.session_type_id ? String(session.session_type_id) : '',
      speaker_ids: (session.speakers || []).map(function(s) { return s.id; }),
      track_tag_ids: (session.tracks || []).map(function(tr) { return tr.id; }),
      title: title,
      desc: desc,
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
            t('All times in') + ' ' + formatTimezoneLabel(timezone, event && event.start_date)
          )
        ),
        React.createElement('button', {
          onClick: self.handleNewSession,
          className: 'flex items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary/90 transition-colors shadow-sm'
        },
          React.createElement('i', { className: 'fas fa-plus', style: { fontSize: 14 } }),
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
            React.createElement('i', { className: 'fas fa-calendar-alt text-muted-foreground/50 mb-3 mx-auto block', style: { fontSize: 40 } }),
            React.createElement('p', { className: 'text-muted-foreground text-sm mb-4' }, t('No sessions for this day yet.')),
            React.createElement('button', {
              onClick: self.handleNewSession,
              className: 'bg-primary text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary/90 transition-colors'
            }, t('Add First Session'))
          )
        : React.createElement(ProgrammeSchedule, {
            sessions: sessionsForDay,
            timezone: timezone,
            t: t,
            renderActions: function(session) {
              return renderSessionActions(session, { onEdit: self.handleEdit, onDelete: self.handleDelete }, t);
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
        languages: self.getLanguages(),
        t: t,
        onClose: self.handleCloseModal,
        onSaved: self.handleSaved,
        onSpeakerCreated: function(spk) {
          self.setState(function(prev) {
            return { speakers: prev.speakers.concat([spk]) };
          });
        },
        onSpeakerUpdated: function(spk) {
          self.setState(function(prev) {
            return {
              speakers: prev.speakers.map(function(s) { return s.id === spk.id ? spk : s; }),
              sessions: prev.sessions.map(function(sess) {
                if (!sess.speakers || !sess.speakers.some(function(s) { return s.id === spk.id; })) return sess;
                return Object.assign({}, sess, {
                  speakers: sess.speakers.map(function(s) {
                    return s.id === spk.id ? Object.assign({}, s, { name: spk.name, photo_url: spk.photo_url }) : s;
                  })
                });
              })
            };
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
