import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import { QRCodeCanvas } from 'qrcode.react';
import { checkinService } from '../../services/eventApp/checkin.service';

class BadgeExport extends Component {
  constructor(props) {
    super(props);
    this.state = {
      badges: null,
      isLoading: true,
      error: null,
      exportMarked: false,
      blankCount: 10,
      blankBadges: null,
      blankLoading: false,
      blankError: null,
    };
  }

  onBlankCountChange = function(e) {
    var value = parseInt(e.target.value, 10);
    this.setState({ blankCount: isNaN(value) ? '' : value });
  }.bind(this);

  generateBlankBadges = function() {
    var eventId = this.props.event && this.props.event.id;
    var count = this.state.blankCount;
    if (!eventId || !count || count < 1) {
      return;
    }
    this.setState({ blankLoading: true, blankError: null });
    checkinService.getBlankBadges(eventId, count).then(function(result) {
      if (result.error) {
        this.setState({ blankLoading: false, blankError: result.error });
      } else {
        this.setState({ blankLoading: false, blankBadges: result.data });
      }
    }.bind(this));
  }.bind(this);

  clearBlankBadges = function() {
    this.setState({ blankBadges: null, blankError: null });
  }.bind(this);

  blankBadgeStyles = function() {
    return (
      <style>{`
        .badge-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
          gap: 16px;
        }
        .badge-card {
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 12px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          background: white;
          page-break-inside: avoid;
        }
        .badge-name {
          font-weight: 600;
          font-size: 13px;
          text-align: center;
          margin: 0;
        }
        .badge-role {
          font-size: 11px;
          color: #64748b;
          text-align: center;
          margin: 0;
        }
        @media print {
          .no-print { display: none !important; }
          .badge-grid {
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
          }
        }
      `}</style>
    );
  };

  markExported = function() {
    var badges = this.state.badges;
    var eventId = this.props.event && this.props.event.id;
    if (!badges || !badges.length || !eventId) {
      return;
    }
    var userIds = badges.map(function(b) { return b.user_id; });
    checkinService.markBadgesExported(eventId, userIds).then(function(result) {
      if (!result.error) {
        this.setState({ exportMarked: true });
      }
    }.bind(this));
  }.bind(this);

  printBadges = function() {
    this.markExported();
    window.print();
  }.bind(this);

  componentDidMount() {
    var eventId = this.props.event && this.props.event.id;
    if (!eventId) {
      this.setState({ isLoading: false, error: 'No event found.' });
      return;
    }
    checkinService.getBadgeExport(eventId).then(function(result) {
      if (result.error) {
        this.setState({ isLoading: false, error: result.error });
      } else {
        this.setState({ isLoading: false, badges: result.data });
      }
    }.bind(this));
  }

  downloadCsv = function() {
    var badges = this.state.badges;
    if (!badges || !badges.length) {
      return;
    }
    var header = ['user_id', 'fullname', 'role', 'token', 'qr_url'];
    var rows = badges.map(function(b) {
      return [b.user_id, '"' + b.fullname + '"', '"' + b.role + '"', b.token, b.qr_url].join(',');
    });
    var csv = [header.join(',')].concat(rows).join('\n');
    var blob = new Blob([csv], { type: 'text/csv' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'badges.csv';
    a.click();
    URL.revokeObjectURL(url);
    this.markExported();
  }.bind(this);

  render() {
    var t = this.props.t;
    var badges = this.state.badges;
    var isLoading = this.state.isLoading;
    var error = this.state.error;

    if (isLoading) {
      return (
        <div className="d-flex justify-content-center py-8">
          <div className="spinner-border" role="status">
            <span className="sr-only">{t('Loading...')}</span>
          </div>
        </div>
      );
    }

    if (error) {
      return <div className="alert alert-danger mt-4">{error}</div>;
    }

    var blankBadges = this.state.blankBadges;

    // Dedicated blank-badge view: QR-only badges carrying fresh random tokens
    // that a volunteer can later link to an attendee. Shown exclusively so that
    // printing here produces only blanks, not the named attendee badges.
    if (blankBadges) {
      return (
        <div className="py-6 px-4">
          <div className="flex items-center justify-between mb-6 no-print">
            <h1 className="text-2xl font-bold text-foreground">
              {t('Blank Badges')} ({blankBadges.length})
            </h1>
            <div className="flex gap-3">
              <button
                className="px-4 py-2 rounded-lg border border-border text-sm font-medium text-foreground hover:bg-surface-low transition-all"
                onClick={this.clearBlankBadges}
              >
                {t('Back to badges')}
              </button>
              <button
                className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-container transition-all"
                onClick={function() { window.print(); }}
              >
                {t('Print Blank Badges')}
              </button>
            </div>
          </div>

          <div className="alert alert-info mb-6 no-print">
            {t('These are blank badges. Print them, then link one to an attendee whose badge was not printed by scanning it at the registration desk or check-in console.')}
          </div>

          <div className="badge-grid">
            {blankBadges.map(function(badge, idx) {
              return (
                <div key={badge.token} className="badge-card">
                  <QRCodeCanvas value={badge.qr_url} size={140} includeMargin={false} />
                  <p className="badge-name">{t('Blank Badge')}</p>
                  <p className="badge-role">#{idx + 1}</p>
                </div>
              );
            })}
          </div>

          {this.blankBadgeStyles()}
        </div>
      );
    }

    if (!badges || !badges.length) {
      return <div className="alert alert-warning mt-4">{t('No guests found.')}</div>;
    }

    return (
      <div className="py-6 px-4">
        <div className="flex items-center justify-between mb-6 no-print">
          <h1 className="text-2xl font-bold text-foreground">{t('Badge Export')}</h1>
          <div className="flex gap-3">
            <button
              className="px-4 py-2 rounded-lg border border-border text-sm font-medium text-foreground hover:bg-surface-low transition-all"
              onClick={this.downloadCsv}
            >
              {t('Download CSV')}
            </button>
            <button
              className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-container transition-all"
              onClick={this.printBadges}
            >
              {t('Print Badges')}
            </button>
          </div>
        </div>

        <div className="flex flex-wrap items-end gap-3 mb-6 p-4 rounded-xl border border-border bg-surface-low no-print">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-foreground">{t('Blank badges to generate')}</label>
            <input
              type="number"
              min="1"
              value={this.state.blankCount}
              onChange={this.onBlankCountChange}
              className="w-28 px-3 py-2 rounded-lg border border-border text-sm text-foreground"
            />
          </div>
          <button
            className="px-4 py-2 rounded-lg border border-primary text-primary text-sm font-semibold hover:bg-primary/10 transition-all disabled:opacity-50"
            onClick={this.generateBlankBadges}
            disabled={this.state.blankLoading}
          >
            {this.state.blankLoading ? t('Generating...') : t('Generate blank badges')}
          </button>
          {this.state.blankError && (
            <span className="text-sm text-error">{this.state.blankError}</span>
          )}
        </div>

        {this.state.exportMarked && (
          <div className="alert alert-success mb-6 no-print">
            {t('Badges marked as printed — check-in will no longer warn for these attendees.')}
          </div>
        )}

        <div className="badge-grid">
          {badges.map(function(badge) {
            return (
              <div key={badge.user_id} className="badge-card">
                <QRCodeCanvas value={badge.qr_url} size={140} includeMargin={false} />
                <p className="badge-name">{badge.fullname}</p>
                <p className="badge-role">{badge.role}</p>
              </div>
            );
          })}
        </div>

        {this.blankBadgeStyles()}
      </div>
    );
  }
}

export default withTranslation()(BadgeExport);
