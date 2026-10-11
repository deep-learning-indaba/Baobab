import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Modal from '../../../components/Modal';
import { Button } from '../../../components/ui/button';
import { linkFields, liquidString } from './schema';

const CUSTOM = '__custom__';

/** Collects a label and a link and inserts a {% button %} tag. */
export default function ButtonDialog({ visible, context, onInsert, onClose }) {
  const { t } = useTranslation();
  const links = linkFields(context);
  const [label, setLabel] = useState('');
  const [link, setLink] = useState('');
  const [customUrl, setCustomUrl] = useState('https://');
  const [style, setStyle] = useState('primary');

  useEffect(() => {
    if (visible) {
      setLabel('');
      setLink(links.length ? links[0].path : CUSTOM);
      setCustomUrl('https://');
      setStyle('primary');
    }
    // links is derived from context, which doesn't change while open.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  const customValid = /^(https?:\/\/|mailto:)\S+$/.test(customUrl);
  const canInsert = label.trim() && (link !== CUSTOM || customValid);

  const insert = () => {
    const target = link === CUSTOM ? liquidString(customUrl.trim()) : link;
    const styleArg = style === 'secondary' ? ', style: "secondary"' : '';
    onInsert(`\n{% button ${liquidString(label.trim())}, ${target}${styleArg} %}\n`);
  };

  return (
    <Modal visible={visible} onClickBackdrop={onClose}>
      <h2 className="font-heading text-lg font-semibold text-foreground">{t('Add a button')}</h2>
      <label className="block text-sm">
        <span className="font-medium text-foreground">{t('Button text')}</span>
        <input
          className="mt-1 w-full rounded-lg border border-border px-3 py-2 text-sm"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder={t('e.g. Accept my offer')}
          autoFocus
        />
      </label>
      <label className="block text-sm">
        <span className="font-medium text-foreground">{t('Links to')}</span>
        <select
          className="mt-1 w-full rounded-lg border border-border px-3 py-2 text-sm bg-white"
          value={link}
          onChange={(e) => setLink(e.target.value)}
        >
          {links.map(({ path, field }) => (
            <option key={path} value={path}>{`${field.description} (${path})`}</option>
          ))}
          <option value={CUSTOM}>{t('Another web address…')}</option>
        </select>
      </label>
      {link === CUSTOM && (
        <label className="block text-sm">
          <span className="font-medium text-foreground">{t('Web address')}</span>
          <input
            className="mt-1 w-full rounded-lg border border-border px-3 py-2 text-sm font-mono"
            value={customUrl}
            onChange={(e) => setCustomUrl(e.target.value)}
          />
          {!customValid && (
            <span className="text-xs text-error">{t('Must start with https://, http:// or mailto:')}</span>
          )}
        </label>
      )}
      <fieldset className="text-sm">
        <legend className="font-medium text-foreground mb-1">{t('Style')}</legend>
        <div className="flex gap-4">
          {[['primary', t('Filled')], ['secondary', t('Outline')]].map(([value, text]) => (
            <label key={value} className="inline-flex items-center gap-2 cursor-pointer">
              <input type="radio" name="button-style" value={value} checked={style === value}
                onChange={() => setStyle(value)} />
              {text}
            </label>
          ))}
        </div>
      </fieldset>
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="outline" onClick={onClose}>{t('Cancel')}</Button>
        <Button onClick={insert} disabled={!canInsert}>{t('Insert button')}</Button>
      </div>
    </Modal>
  );
}
