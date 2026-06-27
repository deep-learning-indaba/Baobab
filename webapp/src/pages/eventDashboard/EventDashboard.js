import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import EventStats from '../eventStats';
import { Card } from '../../components/ui/card';

class EventDashboard extends Component {
  render() {
    const { event, t } = this.props;

    return (
      <div className="py-6 max-w-5xl mx-auto space-y-6">
        <Card className="p-8 rounded-2xl shadow-sm border border-border bg-white">
          <h1 className="font-heading text-3xl font-bold text-foreground mb-2">
            {t('Dashboard')}
          </h1>
          <p className="text-muted-foreground">{event.description}</p>
        </Card>
        <EventStats event={event} />
      </div>
    );
  }
}

export default withTranslation()(EventDashboard);
