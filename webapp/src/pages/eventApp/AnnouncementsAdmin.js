import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import { announcementService } from '../../services/eventApp/announcement.service';
import { formatInEventTz } from '../../utils/datetime';
import MarkdownRenderer from '../../components/MarkdownRenderer';
import TranslatableFieldGroup from '../formEditor/components/TranslatableFieldGroup';

var TABS = { COMPOSE: 'compose', DASHBOARD: 'dashboard' };
var DEFAULT_LANGUAGES = [{ code: 'en', description: 'English' }];

class AnnouncementsAdmin extends Component {
  constructor(props) {
    super(props);
    this.state = {
      tab: TABS.COMPOSE,

      // Compose form — keyed by language code, e.g. { en: '...', fr: '...' }
      title: {},
      body: {},
      expiryDate: '',
      expiryTime: '',
      critical: false,
      targetAudience: 'checked_in',
      isSending: false,
      showConfirm: false,
      sendError: null,
      sendSuccess: null,
      audienceCount: null,

      // Dashboard
      adminList: [],
      isLoadingAdmin: false,
      adminError: null,
    };
    this.handleSend = this.handleSend.bind(this);
    this.handleConfirmSend = this.handleConfirmSend.bind(this);
    this.handleFieldChange = this.handleFieldChange.bind(this);
    this.handleTabChange = this.handleTabChange.bind(this);
    this.handleDelete = this.handleDelete.bind(this);
  }

  getLanguages() {
    return (this.props.organisation && this.props.organisation.languages) || DEFAULT_LANGUAGES;
  }

  getPrimaryLanguage() {
    return this.getLanguages()[0].code;
  }

  handleTabChange(tab) {
    this.setState({ tab: tab });
    if (tab === TABS.DASHBOARD) this.loadAdmin();
  }

  loadAdmin() {
    var self = this;
    var event = this.props.event;
    if (!event) return;
    var language = (this.props.i18n && this.props.i18n.language || 'en').slice(0, 2);
    self.setState({ isLoadingAdmin: true, adminError: null });
    announcementService.listAdmin(event.id, language).then(function(result) {
      self.setState({
        isLoadingAdmin: false,
        adminList: result.error ? [] : (result.data || []),
        adminError: result.error || null,
      });
    });
  }

  handleFieldChange(fieldName, lang, value) {
    this.setState(function(prev) {
      var next = Object.assign({}, prev[fieldName]);
      next[lang] = value;
      var update = { sendSuccess: null };
      update[fieldName] = next;
      return update;
    });
  }

  handleSend() {
    var primaryLang = this.getPrimaryLanguage();
    if (!(this.state.title[primaryLang] || '').trim()) return;
    this.setState({ showConfirm: true, sendError: null, sendSuccess: null });
  }

  handleConfirmSend() {
    var self = this;
    var event = this.props.event;
    if (!event) return;

    var expiryAt = null;
    if (this.state.expiryDate) {
      var dateStr = this.state.expiryDate + 'T' + (this.state.expiryTime || '23:59') + ':00';
      var local = new Date(dateStr);
      if (!isNaN(local.getTime())) expiryAt = local.toISOString();
    }

    var translations = this.getLanguages()
      .map(function(lang) {
        return {
          language: lang.code,
          title: (self.state.title[lang.code] || '').trim(),
          body_markdown: self.state.body[lang.code] || '',
        };
      })
      .filter(function(t) { return t.title; });

    var payload = {
      event_id: event.id,
      translations: translations,
      expiry_at: expiryAt,
      critical: this.state.critical,
      target_audience: this.state.targetAudience,
    };

    self.setState({ isSending: true, showConfirm: false });
    announcementService.create(payload).then(function(result) {
      if (result.error) {
        self.setState({ isSending: false, sendError: result.error });
      } else {
        self.setState({
          isSending: false,
          sendSuccess: true,
          audienceCount: result.data && result.data.audience_count,
          title: {}, body: {},
          expiryDate: '', expiryTime: '', critical: false, targetAudience: 'checked_in',
        });
      }
    });
  }

  handleDelete(id) {
    var self = this;
    var event = this.props.event;
    if (!event) return;
    announcementService.remove(id, event.id).then(function() {
      self.setState(function(prev) {
        return { adminList: prev.adminList.filter(function(a) { return a.id !== id; }) };
      });
    });
  }

  render() {
    var t = this.props.t;
    var event = this.props.event;
    var timezone = (event && event.timezone) || 'UTC';
    var s = this.state;
    var languages = this.getLanguages();
    var primaryLang = this.getPrimaryLanguage();
    var isMultiLingual = languages.length > 1;
    var primaryTitle = s.title[primaryLang] || '';
    var primaryBody = s.body[primaryLang] || '';

    return (
      <div className="w-full max-w-5xl mx-auto pt-6 space-y-6">
        <h1 className="font-heading text-2xl font-bold text-foreground text-left">{t('Announcements Admin')}</h1>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-border">
          {[TABS.COMPOSE, TABS.DASHBOARD].map(function(tab) {
            var label = tab === TABS.COMPOSE ? t('Compose') : t('Dashboard');
            return (
              <button
                key={tab}
                onClick={function() { this.handleTabChange(tab); }.bind(this)}
                className={'pb-2 px-1 text-sm font-medium border-b-2 transition-colors ' + (s.tab === tab ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground')}
              >
                {label}
              </button>
            );
          }, this)}
        </div>

        {/* Compose tab */}
        {s.tab === TABS.COMPOSE && (
          <div className="space-y-5">
            {s.sendSuccess && (
              <div className="bg-green-50 border border-green-200 text-green-800 rounded-xl p-4 text-sm">
                {t('Announcement sent to {{count}} attendees.', { count: s.audienceCount || 0 })}
              </div>
            )}
            {s.sendError && (
              <div className="bg-red-50 border border-red-200 text-destructive rounded-xl p-4 text-sm">{s.sendError}</div>
            )}

            <div className="bg-white rounded-2xl border border-border p-5 space-y-4">
              <TranslatableFieldGroup
                label={isMultiLingual ? t('Title') + ' *' : t('Title')}
                fieldName="title"
                values={s.title}
                languages={languages}
                onChange={function(lang, value) { this.handleFieldChange('title', lang, value); }.bind(this)}
                autoTranslateEnabled={isMultiLingual}
                placeholder={t('Announcement title')}
              />
              <TranslatableFieldGroup
                label={t('Body')}
                fieldName="body"
                values={s.body}
                languages={languages}
                onChange={function(lang, value) { this.handleFieldChange('body', lang, value); }.bind(this)}
                autoTranslateEnabled={isMultiLingual}
                multiline={true}
                placeholder={t('Supports Markdown formatting...')}
              />
              {primaryBody && (
                <div className="mt-2 p-3 bg-muted/30 rounded-lg border border-border">
                  <p className="text-xs text-muted-foreground mb-1">{t('Preview')}</p>
                  <div className="text-sm">
                    <MarkdownRenderer source={primaryBody} />
                  </div>
                </div>
              )}
            </div>

            <div className="bg-white rounded-2xl border border-border p-5 space-y-4">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{t('Options')}</p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">{t('Expiry date')}</label>
                  <input
                    type="date"
                    className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                    value={s.expiryDate}
                    onChange={function(e) { this.setState({ expiryDate: e.target.value }); }.bind(this)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">{t('Expiry time')}</label>
                  <input
                    type="time"
                    className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                    value={s.expiryTime}
                    onChange={function(e) { this.setState({ expiryTime: e.target.value }); }.bind(this)}
                  />
                </div>
              </div>
              <div className="flex items-center gap-3">
                <input
                  id="critical-toggle"
                  type="checkbox"
                  className="rounded"
                  checked={s.critical}
                  onChange={function(e) { this.setState({ critical: e.target.checked }); }.bind(this)}
                />
                <label htmlFor="critical-toggle" className="text-sm text-foreground">
                  {t('Critical (send email)')}
                  <span className="block text-xs text-muted-foreground mt-0.5">
                    {t('Sends an email in addition to push and inbox')}
                  </span>
                </label>
              </div>
              <div className="flex items-center gap-3">
                <button
                  id="audience-toggle"
                  role="switch"
                  aria-checked={s.targetAudience === 'guest_list'}
                  onClick={function() {
                    this.setState(function(prev) {
                      return { targetAudience: prev.targetAudience === 'checked_in' ? 'guest_list' : 'checked_in' };
                    });
                  }.bind(this)}
                  className={'relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-primary/40 ' + (s.targetAudience === 'guest_list' ? 'bg-primary' : 'bg-muted')}
                >
                  <span className={'pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ' + (s.targetAudience === 'guest_list' ? 'translate-x-4' : 'translate-x-0')} />
                </button>
                <label htmlFor="audience-toggle" className="text-sm text-foreground cursor-pointer" onClick={function() {
                  this.setState(function(prev) {
                    return { targetAudience: prev.targetAudience === 'checked_in' ? 'guest_list' : 'checked_in' };
                  });
                }.bind(this)}>
                  {t('Send to all guests')}
                  <span className="block text-xs text-muted-foreground mt-0.5">
                    {s.targetAudience === 'guest_list'
                      ? t('Sending to everyone on the guest list, including those not yet checked in')
                      : t('Sending to checked-in guests only (default)')}
                  </span>
                </label>
              </div>
            </div>

            <button
              onClick={this.handleSend}
              disabled={s.isSending || !primaryTitle.trim()}
              className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary-container disabled:opacity-50 transition-all"
            >
              {s.isSending ? t('Sending...') : t('Send announcement')}
            </button>
          </div>
        )}

        {/* Dashboard tab */}
        {s.tab === TABS.DASHBOARD && (
          <div className="space-y-4">
            {s.isLoadingAdmin && (
              <p className="text-center text-muted-foreground py-8">{t('Loading')}</p>
            )}
            {s.adminError && (
              <p className="text-center text-destructive py-4">{s.adminError}</p>
            )}
            {!s.isLoadingAdmin && !s.adminError && s.adminList.length === 0 && (
              <p className="text-center text-muted-foreground py-8">{t('No announcements sent yet.')}</p>
            )}
            {s.adminList.map(function(ann) {
              return (
                <div key={ann.id} className="bg-white rounded-2xl border border-border shadow-sm p-4 space-y-2">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-foreground truncate">{ann.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {ann.sent_at ? formatInEventTz(ann.sent_at, timezone, { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''}
                        {ann.expiry_at && (
                          <span className="ml-2 text-muted-foreground/60">
                            · {t('Expires')} {formatInEventTz(ann.expiry_at, timezone, { day: 'numeric', month: 'short' })}
                          </span>
                        )}
                      </p>
                    </div>
                    <button
                      onClick={function() { this.handleDelete(ann.id); }.bind(this)}
                      className="text-muted-foreground hover:text-destructive transition-colors flex-shrink-0"
                      title={t('Delete')}
                    >
                      <i className="fas fa-trash-alt" style={{ fontSize: 15 }} />
                    </button>
                  </div>
                  <div className="flex gap-4 text-xs text-muted-foreground">
                    <span>
                      <span className="font-semibold text-foreground">{ann.delivered_count}</span> {t('Delivered')}
                    </span>
                    <span>
                      <span className="font-semibold text-foreground">{ann.opened_count}</span> {t('Opened')}
                    </span>
                    {ann.delivered_count > 0 && (
                      <span className="text-muted-foreground/70">
                        ({Math.round(ann.opened_count / ann.delivered_count * 100)}% {t('open rate')})
                      </span>
                    )}
                  </div>
                </div>
              );
            }, this)}
          </div>
        )}

        {/* Send confirmation modal */}
        {s.showConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
            <div className="bg-white rounded-2xl shadow-xl p-6 max-w-sm w-full mx-4 space-y-4">
              <h2 className="text-lg font-bold text-foreground">{t('Confirm send')}</h2>
              <p className="text-sm text-foreground/80">
                {s.targetAudience === 'guest_list'
                  ? t('This will notify all guests on the guest list (including those not yet checked in) via push notification and inbox.')
                  : t('This will notify all currently checked-in attendees via push notification and inbox.')}
                {s.critical && (
                  <span className="block mt-1 text-amber-700">{t('Critical: email will also be sent.')}</span>
                )}
              </p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={function() { this.setState({ showConfirm: false }); }.bind(this)}
                  className="px-4 py-2 rounded-lg border border-border text-sm font-medium text-foreground hover:bg-muted/50 transition-colors"
                >
                  {t('Cancel')}
                </button>
                <button
                  onClick={this.handleConfirmSend}
                  className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-container transition-colors"
                >
                  {t('Send')}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }
}

export default withTranslation()(AnnouncementsAdmin);
