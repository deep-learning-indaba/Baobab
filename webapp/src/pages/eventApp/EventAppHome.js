import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { eventService } from '../../services/events';
import { announcementService } from '../../services/eventApp/announcement.service';
import { formatInEventTz } from '../../utils/datetime';

class EventAppHome extends Component {
  constructor(props) {
    super(props);
    this.state = { links: [], announcements: [], isLoading: true };
  }

  componentDidMount() {
    var self = this;
    var event = this.props.event;
    var language = (this.props.i18n && this.props.i18n.language) || 'en';
    Promise.all([
      eventService.getResourceLinks(event.id, language),
      announcementService.listActive(event.id, language),
    ]).then(function(results) {
      self.setState({
        links: results[0].links || [],
        announcements: results[1].data || [],
        isLoading: false,
      });
    });
  }

  render() {
    var t = this.props.t;
    var event = this.props.event;
    var timezone = (event && event.timezone) || 'UTC';
    var eventKey = event && event.key;
    var links = this.state.links;
    var announcements = this.state.announcements;
    var isLoading = this.state.isLoading;

    return (
      React.createElement('div', { className: 'w-full max-w-5xl mx-auto pt-6 space-y-6' },
        React.createElement('h1', { className: 'font-heading text-2xl font-bold text-foreground' }, event.name),

        // Active announcements banner
        !isLoading && announcements.length > 0 && React.createElement('div', { className: 'space-y-3' },
          announcements.map(function(ann) {
            return React.createElement(Link, {
              key: ann.id,
              to: '/' + eventKey + '/event-app/announcements/' + ann.id,
              className: 'block bg-primary/5 border border-primary/20 rounded-2xl p-4 hover:border-primary/40 transition-all'
            },
              React.createElement('div', { className: 'flex items-start gap-3' },
                React.createElement('div', { className: 'mt-0.5 flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center' },
                  React.createElement('i', { className: 'fas fa-bell text-primary', style: { fontSize: 16 } })
                ),
                React.createElement('div', { className: 'min-w-0 flex-1' },
                  React.createElement('p', { className: 'font-semibold text-sm text-foreground' }, ann.title),
                  React.createElement('p', { className: 'text-xs text-muted-foreground mt-0.5' },
                    ann.sent_at ? formatInEventTz(ann.sent_at, timezone, { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' }) : ''
                  ),
                  ann.body_markdown && React.createElement('p', { className: 'text-xs text-foreground/70 mt-1 line-clamp-2' }, ann.body_markdown)
                )
              )
            );
          })
        ),

        // Resource links
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
