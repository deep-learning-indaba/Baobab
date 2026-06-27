import React, { Component } from 'react';
import { withTranslation } from 'react-i18next';
import { eventService } from '../../services/events';
import { Card } from '../../components/ui/card';
import { ConfirmModal } from '../../components/Modal';

const EMPTY_LINK = { title_en: '', title_fr: '', url: '', category: '', icon: '', sort_order: '' };

const ICON_GROUPS = [
  {
    label: 'Documents',
    icons: [
      { cls: 'fas fa-file-pdf', label: 'PDF' },
      { cls: 'fas fa-file-alt', label: 'Document' },
      { cls: 'fas fa-file-word', label: 'Word' },
      { cls: 'fas fa-file-excel', label: 'Spreadsheet' },
      { cls: 'fas fa-file-powerpoint', label: 'Slides' },
      { cls: 'fas fa-file-image', label: 'Image file' },
      { cls: 'fas fa-file', label: 'File' },
      { cls: 'fas fa-download', label: 'Download' },
    ],
  },
  {
    label: 'Web',
    icons: [
      { cls: 'fas fa-link', label: 'Link' },
      { cls: 'fas fa-external-link-alt', label: 'External link' },
      { cls: 'fas fa-globe', label: 'Website' },
      { cls: 'fas fa-wifi', label: 'WiFi' },
    ],
  },
  {
    label: 'Travel',
    icons: [
      { cls: 'fas fa-plane', label: 'Flight' },
      { cls: 'fas fa-hotel', label: 'Hotel' },
      { cls: 'fas fa-map-marker-alt', label: 'Location' },
      { cls: 'fas fa-map', label: 'Map' },
      { cls: 'fas fa-bus', label: 'Bus' },
      { cls: 'fas fa-train', label: 'Train' },
      { cls: 'fas fa-car', label: 'Car' },
      { cls: 'fas fa-taxi', label: 'Taxi' },
    ],
  },
  {
    label: 'Event',
    icons: [
      { cls: 'fas fa-calendar-alt', label: 'Calendar' },
      { cls: 'fas fa-clock', label: 'Time' },
      { cls: 'fas fa-calendar-check', label: 'Schedule' },
      { cls: 'fas fa-users', label: 'Attendees' },
      { cls: 'fas fa-chalkboard', label: 'Presentation' },
      { cls: 'fas fa-award', label: 'Award' },
      { cls: 'fas fa-certificate', label: 'Certificate' },
      { cls: 'fas fa-trophy', label: 'Trophy' },
    ],
  },
  {
    label: 'Information',
    icons: [
      { cls: 'fas fa-info-circle', label: 'Info' },
      { cls: 'fas fa-question-circle', label: 'FAQ' },
      { cls: 'fas fa-book', label: 'Guide' },
      { cls: 'fas fa-book-open', label: 'Handbook' },
      { cls: 'fas fa-newspaper', label: 'News' },
      { cls: 'fas fa-graduation-cap', label: 'Education' },
      { cls: 'fas fa-briefcase', label: 'Business' },
      { cls: 'fas fa-building', label: 'Venue' },
    ],
  },
  {
    label: 'Social & Comms',
    icons: [
      { cls: 'fas fa-envelope', label: 'Email' },
      { cls: 'fas fa-phone', label: 'Phone' },
      { cls: 'fas fa-comments', label: 'Chat' },
      { cls: 'fas fa-video', label: 'Video call' },
      { cls: 'fab fa-youtube', label: 'YouTube' },
      { cls: 'fab fa-twitter', label: 'Twitter' },
      { cls: 'fab fa-linkedin', label: 'LinkedIn' },
      { cls: 'fab fa-slack', label: 'Slack' },
      { cls: 'fab fa-whatsapp', label: 'WhatsApp' },
      { cls: 'fab fa-github', label: 'GitHub' },
    ],
  },
];

function iconClassName(icon) {
  if (!icon) return null;
  if (icon.includes(' ')) return icon;
  if (icon.startsWith('fa')) return `fas ${icon}`;
  return null;
}

class ResourceLinksAdmin extends Component {
  constructor(props) {
    super(props);
    this.state = {
      links: [],
      isLoading: true,
      error: null,
      formVisible: false,
      formError: null,
      isSaving: false,
      editingLink: null,
      confirmDeleteId: null,
    };
  }

  componentDidMount() {
    this.loadLinks();
  }

  loadLinks = () => {
    const { event } = this.props;
    eventService.getResourceLinks(event.id, 'en').then(result => {
      this.setState({ links: result.links || [], isLoading: false, error: result.error || null });
    });
  };

  hasFrench = () => {
    const { organisation } = this.props;
    return organisation && organisation.languages && organisation.languages.some(l => l.code === 'fr');
  };

  openAdd = () => {
    this.setState({ formVisible: true, editingLink: { ...EMPTY_LINK }, formError: null });
  };

  openEdit = (link) => {
    this.setState({
      formVisible: true,
      editingLink: {
        id: link.id,
        title_en: link.title_en || '',
        title_fr: link.title_fr || '',
        url: link.url || '',
        category: link.category || '',
        icon: link.icon || '',
        sort_order: link.sort_order != null ? String(link.sort_order) : '',
      },
      formError: null,
    });
  };

  cancelForm = () => {
    this.setState({ formVisible: false, editingLink: null, formError: null });
  };

  setField = (field, value) => {
    this.setState(prev => ({ editingLink: { ...prev.editingLink, [field]: value } }));
  };

  saveLink = () => {
    const { editingLink } = this.state;
    const { event, t } = this.props;

    if (!editingLink.title_en.trim()) {
      this.setState({ formError: t('Title (English) is required') });
      return;
    }
    if (!editingLink.url.trim()) {
      this.setState({ formError: t('URL is required') });
      return;
    }

    const payload = {
      event_id: event.id,
      title_en: editingLink.title_en.trim(),
      title_fr: editingLink.title_fr.trim() || undefined,
      url: editingLink.url.trim(),
      category: editingLink.category.trim() || undefined,
      icon: editingLink.icon.trim() || undefined,
      sort_order: editingLink.sort_order !== '' ? parseInt(editingLink.sort_order, 10) : undefined,
    };

    this.setState({ isSaving: true, formError: null });

    const call = editingLink.id
      ? eventService.updateResourceLink({ ...payload, id: editingLink.id })
      : eventService.createResourceLink(payload);

    call.then(result => {
      if (result.error) {
        this.setState({ isSaving: false, formError: result.error });
        return;
      }
      this.setState({ isSaving: false, formVisible: false, editingLink: null }, this.loadLinks);
    });
  };

  confirmDelete = (id) => {
    this.setState({ confirmDeleteId: id });
  };

  deleteLink = () => {
    const { confirmDeleteId } = this.state;
    const { event } = this.props;
    eventService.deleteResourceLink(event.id, confirmDeleteId).then(result => {
      this.setState(prev => ({
        confirmDeleteId: null,
        links: result.error ? prev.links : prev.links.filter(l => l.id !== confirmDeleteId),
        error: result.error || null,
      }));
    });
  };

  renderIconPicker() {
    const { t } = this.props;
    const { editingLink } = this.state;
    const selected = editingLink.icon;

    const isPickerIcon = (value) => ICON_GROUPS.some(g => g.icons.some(ic => ic.cls === value));
    const isCustom = selected && !isPickerIcon(selected);

    return (
      <div className="md:col-span-2 space-y-3">
        <div className="flex items-center justify-between">
          <label className="block text-sm font-semibold text-foreground/90">{t('Icon')}</label>
          {selected && (
            <button
              type="button"
              onClick={() => this.setField('icon', '')}
              className="text-xs text-muted-foreground hover:text-error transition-colors"
            >
              {t('Clear')}
            </button>
          )}
        </div>

        <div className="border border-border rounded-xl bg-white p-4 space-y-4">
          {selected && (
            <div className="flex items-center gap-3 pb-3 border-b border-border/50">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                {iconClassName(selected)
                  ? <i className={`${iconClassName(selected)} text-lg`} />
                  : <span className="text-lg">{selected}</span>
                }
              </div>
              <span className="text-sm text-foreground font-medium">{selected}</span>
            </div>
          )}

          {ICON_GROUPS.map(group => (
            <div key={group.label} className="space-y-2">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">{t(group.label)}</p>
              <div className="flex flex-wrap gap-1.5">
                {group.icons.map(icon => {
                  const isSelected = selected === icon.cls;
                  return (
                    <button
                      key={icon.cls}
                      type="button"
                      title={icon.label}
                      onClick={() => this.setField('icon', isSelected ? '' : icon.cls)}
                      className={`w-9 h-9 rounded-lg flex items-center justify-center transition-all text-sm
                        ${isSelected
                          ? 'bg-primary text-primary-foreground ring-2 ring-primary ring-offset-1'
                          : 'bg-surface-high text-foreground/70 hover:bg-primary/10 hover:text-primary'
                        }`}
                    >
                      <i className={icon.cls} />
                    </button>
                  );
                })}
              </div>
            </div>
          ))}

          <div className="pt-2 border-t border-border/50 space-y-1.5">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">{t('Custom (emoji or FA class)')}</p>
            <input
              className="w-full px-3 py-2 rounded-lg border border-border bg-white text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition"
              value={isCustom ? selected : ''}
              onChange={e => this.setField('icon', e.target.value)}
              placeholder={t('e.g. 📄 or fas fa-star')}
            />
          </div>
        </div>
      </div>
    );
  }

  renderForm() {
    const { t } = this.props;
    const { editingLink, formError, isSaving } = this.state;
    const isEdit = !!editingLink.id;

    const inputClass = "w-full px-3 py-2 rounded-lg border border-border bg-white text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition";
    const labelClass = "block text-sm font-semibold text-foreground/90 mb-1";

    return (
      <div className="mt-6 p-6 bg-slate-50/50 rounded-xl border border-border space-y-5">
        <h3 className="text-lg font-semibold text-foreground/90 pb-2 border-b border-border/50">
          {isEdit ? t('Edit Resource Link') : t('New Resource Link')}
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className={labelClass}>
              <span className="text-error mr-1">*</span>
              {t('Title (English)')}
            </label>
            <input
              className={inputClass}
              value={editingLink.title_en}
              onChange={e => this.setField('title_en', e.target.value)}
              placeholder={t('e.g. Conference Schedule')}
            />
          </div>

          {this.hasFrench() && (
            <div>
              <label className={labelClass}>{t('Title (French)')}</label>
              <input
                className={inputClass}
                value={editingLink.title_fr}
                onChange={e => this.setField('title_fr', e.target.value)}
                placeholder={t('e.g. Programme de la conférence')}
              />
            </div>
          )}

          <div className="md:col-span-2">
            <label className={labelClass}>
              <span className="text-error mr-1">*</span>
              {t('URL')}
            </label>
            <input
              className={inputClass}
              value={editingLink.url}
              onChange={e => this.setField('url', e.target.value)}
              placeholder="https://..."
              type="url"
            />
          </div>

          <div>
            <label className={labelClass}>{t('Category')}</label>
            <input
              className={inputClass}
              value={editingLink.category}
              onChange={e => this.setField('category', e.target.value)}
              placeholder={t('e.g. schedule, visa, travel')}
            />
          </div>

          <div>
            <label className={labelClass}>{t('Sort Order')}</label>
            <input
              className={inputClass}
              value={editingLink.sort_order}
              onChange={e => this.setField('sort_order', e.target.value)}
              placeholder="1"
              type="number"
              min="0"
            />
          </div>

          {this.renderIconPicker()}
        </div>

        {formError && (
          <p className="text-sm text-error">{formError}</p>
        )}

        <div className="flex items-center justify-end gap-3 pt-2 border-t border-border/50">
          <button
            onClick={this.cancelForm}
            className="px-5 py-2.5 rounded-lg text-sm font-semibold bg-surface-high text-foreground hover:bg-surface-high/80 transition-colors"
          >
            {t('Cancel')}
          </button>
          <button
            onClick={this.saveLink}
            disabled={isSaving}
            className="px-5 py-2.5 rounded-lg text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-60"
          >
            {isSaving ? t('Saving...') : t('Save')}
          </button>
        </div>
      </div>
    );
  }

  render() {
    const { t } = this.props;
    const { links, isLoading, error, formVisible, confirmDeleteId } = this.state;

    if (isLoading) {
      return (
        <div className="flex justify-center items-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      );
    }

    return (
      <div className="py-6 max-w-5xl mx-auto space-y-6">
        <Card className="p-8 rounded-2xl shadow-sm border border-border bg-white space-y-6">
          <h1 className="font-heading text-2xl font-bold text-foreground">{t('Resource Links')}</h1>

          {error && (
            <p className="text-sm text-error bg-error/10 border border-error/20 rounded-lg px-4 py-2">{error}</p>
          )}

          {links.length === 0 && !formVisible ? (
            <p className="text-sm text-muted-foreground py-4">{t('No resource links yet.')}</p>
          ) : (
            <div className="divide-y divide-border">
              {links.map(link => {
                const cls = iconClassName(link.icon);
                return (
                  <div key={link.id} className="flex items-center justify-between gap-4 py-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        {link.icon && (
                          <span className="text-muted-foreground text-sm w-5 text-center">
                            {cls ? <i className={cls} /> : link.icon}
                          </span>
                        )}
                        <span className="font-semibold text-sm text-foreground">{link.title_en}</span>
                        {link.category && (
                          <span className="text-xs text-muted-foreground bg-surface-high px-2 py-0.5 rounded-full">{link.category}</span>
                        )}
                      </div>
                      <a
                        href={link.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline truncate block mt-0.5 max-w-sm"
                      >
                        {link.url}
                      </a>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <button
                        onClick={() => this.openEdit(link)}
                        className="text-muted-foreground hover:text-primary transition-colors"
                        title={t('Edit')}
                      >
                        <i className="fa fa-edit text-base" />
                      </button>
                      <button
                        onClick={() => this.confirmDelete(link.id)}
                        className="text-muted-foreground hover:text-error transition-colors"
                        title={t('Delete')}
                      >
                        <i className="fa fa-trash text-base" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {!formVisible && (
            <div className="flex justify-end pt-2">
              <button
                onClick={this.openAdd}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm"
              >
                <i className="fas fa-plus text-xs" />
                {t('Add Resource Link')}
              </button>
            </div>
          )}

          {formVisible && this.renderForm()}
        </Card>

        <ConfirmModal
          visible={confirmDeleteId !== null}
          onOK={this.deleteLink}
          onCancel={() => this.setState({ confirmDeleteId: null })}
          okText={t('Delete')}
          cancelText={t('Cancel')}
        >
          <p>{t('Are you sure you want to delete this resource link?')}</p>
        </ConfirmModal>
      </div>
    );
  }
}

export default withTranslation()(ResourceLinksAdmin);
