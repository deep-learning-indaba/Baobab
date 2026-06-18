import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { attendanceService } from '../../services/attendance';

class ConnectLanding extends Component {
  constructor(props) {
    super(props);
    this.state = { isConfirmedGuest: null, eventLoaded: false };
  }

  componentDidMount() {
    var self = this;
    var event = this.props.event;
    var user = this.props.user;
    if (!event || !user) {
      self.setState({ isConfirmedGuest: false, eventLoaded: true });
      return;
    }
    attendanceService.isConfirmedGuest(event.id).then(function(res) {
      self.setState({
        isConfirmedGuest: res && res.isConfirmedGuest,
        eventLoaded: true,
      });
    }).catch(function() {
      self.setState({ isConfirmedGuest: false, eventLoaded: true });
    });
  }

  render() {
    var t = this.props.t;
    var event = this.props.event;
    var user = this.props.user;
    var location = this.props.location;

    var params = new URLSearchParams(location && location.search);
    var token = params.get('t') || '';
    var eventKey = event && event.key;

    if (!this.state.eventLoaded) {
      return React.createElement('div', { className: 'w-full pt-12 text-center text-muted-foreground' }, t('Loading'));
    }

    // Logged in + confirmed guest → redirect into scan flow
    if (user && this.state.isConfirmedGuest) {
      var scanUrl = '/' + eventKey + '/app/scan' + (token ? '?t=' + encodeURIComponent(token) : '');
      window.location.replace(scanUrl);
      return null;
    }

    // Logged in but not a guest
    if (user && this.state.isConfirmedGuest === false) {
      return (
        <div className="w-full max-w-sm mx-auto pt-16 text-center space-y-4 px-4">
          <h1 className="font-heading text-2xl font-bold text-foreground text-left">{t('Attendees only')}</h1>
          <p className="text-sm text-muted-foreground text-left">
            {t('Scanning badges and connecting is only available to confirmed attendees of {{event}}.', { event: event && event.name })}
          </p>
        </div>
      );
    }

    // Not logged in — branded landing
    var next = encodeURIComponent('/' + eventKey + '/app/scan' + (token ? '?t=' + encodeURIComponent(token) : ''));
    return (
      <div className="w-full max-w-sm mx-auto pt-16 text-center space-y-6 px-4">
        <div className="space-y-2">
          <h1 className="font-heading text-2xl font-bold text-foreground">
            {t('You scanned a badge')}
          </h1>
          <p className="text-muted-foreground text-sm">
            {event && t('Open Baobab to connect with other {{event}} attendees.', { event: event.name })}
          </p>
        </div>
        <div className="space-y-3">
          <Link
            to={'/login?next=' + next}
            className="block w-full py-3 rounded-xl bg-primary text-primary-foreground font-semibold text-sm text-center hover:bg-primary-container transition-colors"
          >
            {t('Log in')}
          </Link>
          <Link
            to={'/createAccount?next=' + next}
            className="block w-full py-3 rounded-xl border border-border text-sm text-center text-foreground hover:bg-muted/50 transition-colors"
          >
            {t('Create account')}
          </Link>
        </div>
        <p className="text-xs text-muted-foreground">
          {t('Already have the app? Open it to connect.')}
        </p>
      </div>
    );
  }
}

export default withTranslation()(ConnectLanding);
