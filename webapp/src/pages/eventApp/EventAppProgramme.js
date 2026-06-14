import React from 'react';
import { withTranslation } from 'react-i18next';

function EventAppProgramme(props) {
  return (
    React.createElement('div', { className: 'w-full max-w-5xl mx-auto pt-6' },
      React.createElement('h1', { className: 'font-heading text-2xl font-bold text-foreground' }, props.t('Programme')),
      React.createElement('p', { className: 'mt-4 text-muted-foreground' }, props.t('Programme coming soon.'))
    )
  );
}

export default withTranslation()(EventAppProgramme);
