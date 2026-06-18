import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import { announcementService } from '../../services/eventApp/announcement.service';
import { translationService } from '../../services/translation/translation.service';
import { formatInEventTz } from '../../utils/datetime';
import MarkdownRenderer from '../../components/MarkdownRenderer';

var TABS = { COMPOSE: 'compose', DASHBOARD: 'dashboard' };

class AnnouncementsAdmin extends Component {
  constructor(props) {
    super(props);
    this.state = {
      tab: TABS.COMPOSE,

      // Compose form
      titleEn: '',
      bodyEn: '',
      titleFr: '',
      bodyFr: '',
      expiryDate: '',
      expiryTime: '',
      critical: false,
      isTranslating: false,
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
    this.handleAutoTranslate = this.handleAutoTranslate.bind(this);
    this.handleTabChange = this.handleTabChange.bind(this);
    this.handleDelete = this.handleDelete.bind(this);
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

  handleAutoTranslate() {
    var self = this;
    var { titleEn, bodyEn } = this.state;
    if (!titleEn && !bodyEn) return;
    self.setState({ isTranslating: true });
    var promises = [];
    if (titleEn) promises.push(translationService.translateText(titleEn, 'en', ['fr']));
    else promises.push(Promise.resolve(null));
    if (bodyEn) promises.push(translationService.translateText(bodyEn, 'en', ['fr']));
    else promises.push(Promise.resolve(null));
    Promise.all(promises).then(function(results) {
      var titleFr = (results[0] && results[0].translated && results[0].translated['fr']) || self.state.titleFr;
      var bodyFr = (results[1] && results[1].translated && results[1].translated['fr']) || self.state.bodyFr;
      self.setState({ titleFr: titleFr, bodyFr: bodyFr, isTranslating: false });
    }).catch(function() {
      self.setState({ isTranslating: false });
    });
  }

  handleSend() {
    if (!this.state.titleEn.trim()) return;
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

    var translations = [{ language: 'en', title: this.state.titleEn, body_markdown: this.state.bodyEn }];
    if (this.state.titleFr.trim()) {
      translations.push({ language: 'fr', title: this.state.titleFr, body_markdown: this.state.bodyFr });
    }

    var payload = {
      event_id: event.id,
      translations: translations,
      expiry_at: expiryAt,
      critical: this.state.critical,
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
          titleEn: '', bodyEn: '', titleFr: '', bodyFr: '',
          expiryDate: '', expiryTime: '', critical: false,
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
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{t('English (required)')}</p>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">{t('Title')}</label>
                <input
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                  value={s.titleEn}
                  onChange={function(e) { this.setState({ titleEn: e.target.value, sendSuccess: null }); }.bind(this)}
                  placeholder={t('Announcement title')}
                  maxLength={200}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">{t('Body')}</label>
                <textarea
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 font-mono"
                  rows={6}
                  value={s.bodyEn}
                  onChange={function(e) { this.setState({ bodyEn: e.target.value, sendSuccess: null }); }.bind(this)}
                  placeholder={t('Supports Markdown formatting...')}
                />
                {s.bodyEn && (
                  <div className="mt-2 p-3 bg-muted/30 rounded-lg border border-border">
                    <p className="text-xs text-muted-foreground mb-1">{t('Preview')}</p>
                    <div className="text-sm">
                      <MarkdownRenderer source={s.bodyEn} />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Auto-translate */}
            <div className="flex justify-center">
              <button
                onClick={this.handleAutoTranslate}
                disabled={s.isTranslating || (!s.titleEn && !s.bodyEn)}
                className="flex items-center gap-2 px-4 py-2 rounded-full border border-primary text-primary text-sm font-medium hover:bg-primary/5 disabled:opacity-40 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m5 8 6 6" /><path d="m4 14 6-6 2-3" /><path d="M2 5h12" /><path d="M7 2h1" />
                  <path d="m22 22-5-10-5 10" /><path d="M14 18h6" />
                </svg>
                {s.isTranslating ? t('Translating...') : t('Auto-translate to French')}
              </button>
            </div>

            <div className="bg-white rounded-2xl border border-border p-5 space-y-4">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{t('French (optional)')}</p>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">{t('Title')}</label>
                <input
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                  value={s.titleFr}
                  onChange={function(e) { this.setState({ titleFr: e.target.value }); }.bind(this)}
                  placeholder={t('Titre de l\'annonce')}
                  maxLength={200}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">{t('Body')}</label>
                <textarea
                  className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 font-mono"
                  rows={6}
                  value={s.bodyFr}
                  onChange={function(e) { this.setState({ bodyFr: e.target.value }); }.bind(this)}
                  placeholder={t('Supports le formatage Markdown...')}
                />
              </div>
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
            </div>

            <button
              onClick={this.handleSend}
              disabled={s.isSending || !s.titleEn.trim()}
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
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14H6L5 6" />
                        <path d="M10 11v6" /><path d="M14 11v6" /><path d="M9 6V4h6v2" />
                      </svg>
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
                {t('This will notify all currently checked-in attendees via push notification and inbox.')}
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
