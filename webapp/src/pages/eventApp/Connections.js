import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import { connectionService } from '../../services/eventApp/connection.service';

var TABS = { REQUESTS: 'requests', SENT: 'sent', CONNECTED: 'connected', SCANNED: 'scanned' };

function Avatar({ photoUrl, firstname, lastname, size }) {
  var sz = size === 'sm' ? 'w-10 h-10 text-base' : 'w-12 h-12 text-lg';
  if (photoUrl) {
    return (
      <img
        src={photoUrl}
        alt={firstname + ' ' + lastname}
        className={sz + ' rounded-full object-cover flex-shrink-0'}
      />
    );
  }
  var initials = (firstname || '?')[0].toUpperCase() + (lastname || '?')[0].toUpperCase();
  return (
    <div className={sz + ' rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary flex-shrink-0'}>
      {initials}
    </div>
  );
}

function PersonRow({ item, eventKey, actions, t }) {
  return (
    <div className="flex items-center gap-3 bg-white rounded-2xl border border-border shadow-sm p-4">
      <Avatar photoUrl={item.photo_url} firstname={item.firstname} lastname={item.lastname} size="sm" />
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-foreground text-sm">{item.firstname} {item.lastname}</p>
        {item.role && <p className="text-xs text-primary">{item.role}</p>}
        {item.headline && <p className="text-xs text-muted-foreground line-clamp-1">{item.headline}</p>}
      </div>
      <div className="flex flex-col gap-1.5 flex-shrink-0">
        {actions}
        <a
          href={'/' + eventKey + '/app/profile/' + item.user_id}
          className="text-xs text-muted-foreground hover:text-primary transition-colors text-center"
        >
          {t('View')}
        </a>
      </div>
    </div>
  );
}

class Connections extends Component {
  constructor(props) {
    super(props);
    this.state = {
      tab: TABS.REQUESTS,
      data: null,
      isLoading: true,
      error: null,
      busyIds: {},
    };
    this.loadData = this.loadData.bind(this);
    this.handleAccept = this.handleAccept.bind(this);
    this.handleReject = this.handleReject.bind(this);
    this.handleBlock = this.handleBlock.bind(this);
    this.handleWithdraw = this.handleWithdraw.bind(this);
  }

  componentDidMount() {
    this.loadData();
  }

  loadData() {
    var self = this;
    var event = this.props.event;
    if (!event) return;
    self.setState({ isLoading: true, error: null });
    connectionService.listConnections(event.id).then(function(res) {
      self.setState({ isLoading: false });
      if (res.error) { self.setState({ error: res.error }); return; }
      self.setState({ data: res.data });
    });
  }

  setBusy(userId, busy) {
    this.setState(function(prev) {
      var updated = Object.assign({}, prev.busyIds);
      if (busy) updated[userId] = true;
      else delete updated[userId];
      return { busyIds: updated };
    });
  }

  removeFromSection(section, userId) {
    this.setState(function(prev) {
      if (!prev.data) return null;
      var updated = Object.assign({}, prev.data);
      updated[section] = (updated[section] || []).filter(function(r) { return r.user_id !== userId; });
      return { data: updated };
    });
  }

  handleAccept(fromUserId) {
    var self = this;
    var event = this.props.event;
    self.setBusy(fromUserId, true);
    connectionService.respond(event.id, fromUserId, 'accept').then(function(res) {
      self.setBusy(fromUserId, false);
      if (!res.error) {
        self.removeFromSection('incoming', fromUserId);
        self.loadData();
      }
    });
  }

  handleReject(fromUserId) {
    var self = this;
    var event = this.props.event;
    self.setBusy(fromUserId, true);
    connectionService.respond(event.id, fromUserId, 'reject').then(function(res) {
      self.setBusy(fromUserId, false);
      if (!res.error) self.removeFromSection('incoming', fromUserId);
    });
  }

  handleBlock(fromUserId) {
    var self = this;
    var event = this.props.event;
    self.setBusy(fromUserId, true);
    connectionService.respond(event.id, fromUserId, 'block').then(function(res) {
      self.setBusy(fromUserId, false);
      if (!res.error) self.removeFromSection('incoming', fromUserId);
    });
  }

  handleWithdraw(toUserId) {
    var self = this;
    var event = this.props.event;
    self.setBusy(toUserId, true);
    connectionService.withdraw(event.id, toUserId).then(function(res) {
      self.setBusy(toUserId, false);
      if (!res.error) self.removeFromSection('outgoing', toUserId);
    });
  }

  render() {
    var t = this.props.t;
    var event = this.props.event;
    var eventKey = event && event.key;
    var s = this.state;
    var data = s.data || { incoming: [], outgoing: [], connected: [], scanned_history: [] };

    var tabs = [
      { key: TABS.REQUESTS, label: t('Requests'), count: data.incoming.length },
      { key: TABS.SENT, label: t('Sent'), count: data.outgoing.length },
      { key: TABS.CONNECTED, label: t('Connections'), count: data.connected.length },
      { key: TABS.SCANNED, label: t('Scanned'), count: data.scanned_history.length },
    ];

    return (
      <div className="w-full max-w-2xl mx-auto pt-6 space-y-4">
        <h1 className="font-heading text-2xl font-bold text-foreground text-left">{t('Connections')}</h1>

        {/* Tabs */}
        <div className="flex gap-1 border-b border-border overflow-x-auto">
          {tabs.map(function(tab) {
            var active = s.tab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={function() { this.setState({ tab: tab.key }); }.bind(this)}
                className={'pb-2 px-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5 whitespace-nowrap ' +
                  (active ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground')}
              >
                {tab.label}
                {tab.count > 0 && (
                  <span className={'text-xs font-bold px-1.5 py-0.5 rounded-full ' +
                    (active ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground')}>
                    {tab.count}
                  </span>
                )}
              </button>
            );
          }, this)}
        </div>

        {s.isLoading && <p className="text-center text-muted-foreground py-8">{t('Loading')}</p>}
        {s.error && <p className="text-center text-destructive py-4">{s.error}</p>}

        {!s.isLoading && s.tab === TABS.REQUESTS && (
          <div className="space-y-3">
            {data.incoming.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-8">{t('No pending connection requests.')}</p>
            )}
            {data.incoming.map(function(item) {
              var busy = !!s.busyIds[item.user_id];
              return (
                <PersonRow
                  key={item.user_id}
                  item={item}
                  eventKey={eventKey}
                  t={t}
                  actions={
                    <div className="flex gap-1.5">
                      <button
                        onClick={function() { this.handleAccept(item.user_id); }.bind(this)}
                        disabled={busy}
                        className="px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-semibold disabled:opacity-50 hover:bg-primary-container transition-colors"
                      >
                        {t('Accept')}
                      </button>
                      <button
                        onClick={function() { this.handleReject(item.user_id); }.bind(this)}
                        disabled={busy}
                        className="px-3 py-1.5 rounded-lg border border-border text-xs text-foreground disabled:opacity-50 hover:bg-muted/50 transition-colors"
                      >
                        {t('Decline')}
                      </button>
                    </div>
                  }
                />
              );
            }, this)}
          </div>
        )}

        {!s.isLoading && s.tab === TABS.SENT && (
          <div className="space-y-3">
            {data.outgoing.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-8">{t('No pending outgoing requests.')}</p>
            )}
            {data.outgoing.map(function(item) {
              var busy = !!s.busyIds[item.user_id];
              return (
                <PersonRow
                  key={item.user_id}
                  item={item}
                  eventKey={eventKey}
                  t={t}
                  actions={
                    <button
                      onClick={function() { this.handleWithdraw(item.user_id); }.bind(this)}
                      disabled={busy}
                      className="px-3 py-1.5 rounded-lg border border-border text-xs text-muted-foreground disabled:opacity-50 hover:text-foreground transition-colors"
                    >
                      {t('Withdraw')}
                    </button>
                  }
                />
              );
            }, this)}
          </div>
        )}

        {!s.isLoading && s.tab === TABS.CONNECTED && (
          <div className="space-y-3">
            {data.connected.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-8">{t('No connections yet. Start by scanning a badge!')}</p>
            )}
            {data.connected.map(function(item) {
              return (
                <PersonRow
                  key={item.user_id}
                  item={item}
                  eventKey={eventKey}
                  t={t}
                  actions={
                    <span className="text-xs text-green-700 font-semibold flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                      {t('Connected')}
                    </span>
                  }
                />
              );
            }, this)}
          </div>
        )}

        {!s.isLoading && s.tab === TABS.SCANNED && (
          <div className="space-y-3">
            {data.scanned_history.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-8">{t('No scanned badges yet.')}</p>
            )}
            {data.scanned_history.map(function(item) {
              var statusLabel = {
                pending: t('Request sent'),
                connected: t('Connected'),
                rejected: t('Not connected'),
                withdrawn: t('Withdrawn'),
                blocked: t('Blocked'),
              }[item.status] || item.status;
              return (
                <PersonRow
                  key={item.user_id}
                  item={item}
                  eventKey={eventKey}
                  t={t}
                  actions={
                    <span className="text-xs text-muted-foreground">{statusLabel}</span>
                  }
                />
              );
            }, this)}
          </div>
        )}
      </div>
    );
  }
}

export default withTranslation()(Connections);
