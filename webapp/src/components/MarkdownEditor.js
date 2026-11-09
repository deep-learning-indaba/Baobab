import React, { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import MarkdownRenderer from './MarkdownRenderer';
import { applyFormat } from './markdownFormatting';

const TOOLBAR = [
  { action: 'heading', icon: 'fa-heading', label: 'Heading', placeholder: 'Heading' },
  { action: 'bold', icon: 'fa-bold', label: 'Bold', placeholder: 'bold text' },
  { action: 'italic', icon: 'fa-italic', label: 'Italic', placeholder: 'italic text' },
  { action: 'link', icon: 'fa-link', label: 'Link', placeholder: 'link text' },
  { action: 'bulletList', icon: 'fa-list-ul', label: 'Bulleted list', placeholder: 'list item' },
  { action: 'numberedList', icon: 'fa-list-ol', label: 'Numbered list', placeholder: 'list item' },
  { action: 'quote', icon: 'fa-quote-right', label: 'Quote', placeholder: 'quote' },
];

const SHORTCUTS = { b: 'bold', i: 'italic', k: 'link' };

function MarkdownEditor({
  value = '',
  onChange,
  onBlur,
  placeholder,
  disabled = false,
  hasError = false,
  ariaLabel,
  previewClassName = '',
  rows = 3,
}) {
  const { t } = useTranslation();
  const [mode, setMode] = useState('write');
  const textareaRef = useRef(null);

  const applyAction = (action) => {
    const textarea = textareaRef.current;
    if (!textarea || disabled) return;
    const item = TOOLBAR.find((i) => i.action === action);
    const edit = applyFormat(
      action,
      value,
      textarea.selectionStart,
      textarea.selectionEnd,
      t(item.placeholder)
    );

    textarea.focus();
    textarea.setSelectionRange(edit.replaceStart, edit.replaceEnd);
    // execCommand keeps the edit on the browser's undo stack and fires a
    // native input event, which React turns into onChange.
    const handled = edit.text === ''
      ? document.execCommand('delete')
      : document.execCommand('insertText', false, edit.text);
    if (handled) {
      // The DOM value already matches what React will render, so the
      // selection can be set straight away and survives the re-render.
      textarea.setSelectionRange(edit.selectionStart, edit.selectionEnd);
      return;
    }

    onChange(value.slice(0, edit.replaceStart) + edit.text + value.slice(edit.replaceEnd));
    // The fallback changes the value through React, so wait for the
    // controlled textarea to re-render before placing the selection.
    requestAnimationFrame(() => {
      if (textareaRef.current) {
        textareaRef.current.setSelectionRange(edit.selectionStart, edit.selectionEnd);
      }
    });
  };

  const handleKeyDown = (e) => {
    if (!(e.ctrlKey || e.metaKey) || e.altKey || e.shiftKey) return;
    const action = SHORTCUTS[e.key.toLowerCase()];
    if (action) {
      e.preventDefault();
      applyAction(action);
    }
  };

  const tabCls = (active) =>
    'px-2.5 py-1 rounded-md text-xs font-semibold cursor-pointer ' +
    (active ? 'bg-primary text-white' : 'bg-surface-low text-foreground hover:bg-surface-high');

  return (
    <div
      className={`w-full border rounded-md text-sm transition-colors focus-within:ring-2 ${
        hasError ? 'border-error focus-within:ring-error/20' : 'border-border focus-within:ring-ring'
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-1 px-2 py-1.5 bg-surface-low rounded-t-md border-b border-border">
        <div className="flex gap-1" role="tablist" aria-label={ariaLabel}>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'write'}
            onClick={() => setMode('write')}
            className={tabCls(mode === 'write')}
          >
            {t('Write')}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'preview'}
            onClick={() => setMode('preview')}
            className={tabCls(mode === 'preview')}
          >
            {t('Preview')}
          </button>
        </div>
        {mode === 'write' && (
          <div className="flex gap-0.5" role="toolbar" aria-label={t('Formatting')}>
            {TOOLBAR.map((item) => (
              <button
                key={item.action}
                type="button"
                title={t(item.label)}
                aria-label={t(item.label)}
                disabled={disabled}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => applyAction(item.action)}
                className="w-7 h-7 rounded-md text-xs text-foreground cursor-pointer hover:bg-surface-high disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <i className={`fas ${item.icon}`} aria-hidden="true"></i>
              </button>
            ))}
          </div>
        )}
      </div>
      {mode === 'write' ? (
        <textarea
          ref={textareaRef}
          className="block w-full px-3 py-2 bg-transparent rounded-b-md text-sm border-0 focus:outline-none resize-y min-h-[80px] disabled:opacity-50 disabled:cursor-not-allowed"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onBlur={onBlur}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={rows}
          aria-label={ariaLabel}
        />
      ) : (
        <div className="px-3 py-2 min-h-[80px]" role="tabpanel">
          {value && value.trim() ? (
            <div className={previewClassName}>
              <MarkdownRenderer source={value} />
            </div>
          ) : (
            <p className="text-muted-foreground italic">{t('Nothing to preview')}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default MarkdownEditor;
