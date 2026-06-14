import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import { eventService } from '../../services/events';

class EventAppHome extends Component {
  constructor(props) {
    super(props);
    this.state = { links: [], isLoading: true, error: null };
  }

  componentDidMount() {
    var language = (this.props.i18n && this.props.i18n.language) || 'en';
    eventService.getResourceLinks(this.props.event.id, language).then(function(result) {
      this.setState({ links: result.links || [], isLoading: false, error: result.error });
    }.bind(this));
  }

  render() {
    var t = this.props.t;
    var event = this.props.event;
    var links = this.state.links;
    var isLoading = this.state.isLoading;

    return (
      React.createElement('div', { className: 'w-full max-w-5xl mx-auto pt-6 space-y-8' },
        React.createElement('h1', { className: 'font-heading text-2xl font-bold text-foreground' }, event.name),
        !isLoading && links.length > 0 && React.createElement('div', { className: 'bg-white rounded-2xl shadow-sm border border-border p-6 space-y-4' },
          React.createElement('h2', { className: 'text-lg font-semibold text-foreground/90' }, t('Resources')),
          React.createElement('ul', { className: 'space-y-2' },
            links.map(function(link) {
              return React.createElement('li', { key: link.id },
                React.createElement('a', { href: link.url, target: '_blank', rel: 'noopener noreferrer', className: 'flex items-center gap-2 text-sm text-primary hover:underline' },
                  link.icon && React.createElement('span', null, link.icon),
                  link.title,
                  link.category && React.createElement('span', { className: 'ml-2 text-xs text-muted-foreground' }, '(' + link.category + ')')
                )
              );
            })
          )
        )
      )
    );
  }
}

export default withTranslation()(EventAppHome);
