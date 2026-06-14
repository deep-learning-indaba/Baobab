import React from 'react';
import { withTranslation } from 'react-i18next';

function EventAppAnnouncements(props) {
  return (
    React.createElement('div', { className: 'w-full max-w-5xl mx-auto pt-6' },
      React.createElement('h1', { className: 'font-heading text-2xl font-bold text-foreground' }, props.t('Announcements')),
      React.createElement('p', { className: 'mt-4 text-muted-foreground' }, props.t('Announcements coming soon.'))
    )
  );
}

export default withTranslation()(EventAppAnnouncements);
