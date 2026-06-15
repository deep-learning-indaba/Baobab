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
    };
  }

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
              onClick={function() { window.print(); }}
            >
              {t('Print Badges')}
            </button>
          </div>
        </div>

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
      </div>
    );
  }
}

export default withTranslation()(BadgeExport);
