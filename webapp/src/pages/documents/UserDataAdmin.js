import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { documentsService } from '../../services/documents';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import Modal from '../../components/Modal';
import Loading from '../../components/Loading';

/**
 * Admin-assigned key/value data per attendee (design section 9.8) - the
 * source for placeholders no form asks about, e.g. a room allocation. A grid
 * of attendees x keys with inline editing, an add-column control, and CSV
 * import (match on email, preview the diff before applying) / export.
 */
const UserDataAdmin = (props) => {
  const { t } = useTranslation();
  const event = props.event;
  const eventKey = event ? event.key : (props.match && props.match.params.eventKey);

  const [keys, setKeys] = useState([]);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newColumnName, setNewColumnName] = useState('');

  const [csvText, setCsvText] = useState(null);
  const [csvFileName, setCsvFileName] = useState('');
  const [importPreview, setImportPreview] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState(null);
  const fileInputRef = useRef(null);

  const load = useCallback(() => {
    if (!event) return;
    setLoading(true);
    documentsService.getUserEventDataGrid(event.id).then((result) => {
      if (result.error) {
        setError(result.error);
      } else {
        setKeys(result.data.keys || []);
        setRows(result.data.rows || []);
        setError(null);
      }
      setLoading(false);
    });
  }, [event]);

  useEffect(() => { load(); }, [load]);

  const handleEditValue = (row, key, value) => {
    documentsService.setUserEventData(event.id, [
      { user_id: row.user_id, key, value },
    ]).then((result) => {
      if (result.error) {
        setError(result.error);
        return;
      }
      setRows((prev) => prev.map((r) => (
        r.user_id === row.user_id ? { ...r, values: { ...r.values, [key]: value } } : r
      )));
    });
  };

  const handleAddColumn = () => {
    const key = newColumnName.trim().toLowerCase().replace(/\s+/g, '_');
    if (!key || keys.includes(key)) return;
    setKeys((prev) => [...prev, key]);
    setNewColumnName('');
  };

  const handleExport = () => {
    documentsService.exportUserEventData(event.id).then((result) => {
      if (result.error) setError(result.error);
    });
  };

  const handleFileChosen = (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    setCsvFileName(file.name);
    setImportError(null);
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || '');
      setCsvText(text);
      documentsService.importUserEventData(event.id, text, false).then((result) => {
        if (result.error) {
          setImportError(result.error);
          return;
        }
        setImportPreview(result.data);
      });
    };
    reader.readAsText(file);
    e.target.value = ''; // allow re-choosing the same file
  };

  const closeImportModal = () => {
    setImportPreview(null);
    setCsvText(null);
    setCsvFileName('');
    setImportError(null);
  };

  const handleApplyImport = () => {
    setImporting(true);
    documentsService.importUserEventData(event.id, csvText, true).then((result) => {
      setImporting(false);
      if (result.error) {
        setImportError(result.error);
        return;
      }
      closeImportModal();
      load();
    });
  };

  if (!event) return <Loading />;

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      <button
        className="text-sm text-action hover:underline mb-2"
        onClick={() => props.history.push(`/${eventKey}/documentsAdmin`)}
      >
        ← {t('Back to Documents')}
      </button>
      <div className="flex items-start justify-between gap-4 mb-1">
        <h1 className="font-heading text-2xl font-semibold text-foreground">{t('Attendee data')}</h1>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="secondary" onClick={handleExport}>{t('Export CSV')}</Button>
          <Button variant="secondary" onClick={() => fileInputRef.current && fileInputRef.current.click()}>
            {t('Import CSV')}
          </Button>
          <input ref={fileInputRef} type="file" accept=".csv,text/csv" className="hidden" onChange={handleFileChosen} />
        </div>
      </div>
      <p className="text-sm text-muted-foreground mb-6">
        {t('Key/value facts about an attendee that no form asks for - e.g. a room allocation - referenced in document templates as {data.key}.')}
      </p>

      {error && <div className="mb-4 rounded-lg border border-error/30 bg-error/5 px-4 py-3 text-sm text-error">{error}</div>}

      <Card className="p-4 mb-6 flex items-center gap-2">
        <input
          className="rounded-lg border border-border px-3 py-2 text-sm w-56"
          placeholder={t('New column key, e.g. hostel')}
          value={newColumnName}
          onChange={(e) => setNewColumnName(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') handleAddColumn(); }}
        />
        <Button variant="secondary" size="sm" onClick={handleAddColumn} disabled={!newColumnName.trim()}>
          {t('+ Add column')}
        </Button>
      </Card>

      {loading ? (
        <Loading />
      ) : rows.length === 0 ? (
        <Card className="p-8 text-center text-muted-foreground">{t('No attendees found for this event yet.')}</Card>
      ) : (
        <Card className="p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground border-b border-border bg-surface-low">
                <th className="py-2 px-4 sticky left-0 bg-surface-low">{t('Person')}</th>
                {keys.map((key) => (
                  <th key={key} className="py-2 px-4 font-mono whitespace-nowrap">{key}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.user_id} className="border-b border-border/50">
                  <td className="py-2 px-4 whitespace-nowrap sticky left-0 bg-white">
                    {row.name || row.email} <span className="text-xs text-muted-foreground">({row.email})</span>
                  </td>
                  {keys.map((key) => (
                    <td key={key} className="py-2 px-4">
                      <input
                        className="rounded-md border border-border px-2 py-1 text-sm w-32"
                        defaultValue={row.values[key] || ''}
                        onBlur={(e) => {
                          if (e.target.value !== (row.values[key] || '')) handleEditValue(row, key, e.target.value);
                        }}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      <Modal visible={!!importPreview} onClickBackdrop={closeImportModal}>
        <h3 className="font-heading font-semibold text-foreground">{t('Import preview')}</h3>
        <p className="text-sm text-muted-foreground">{csvFileName}</p>
        {importError && <p className="text-sm text-error">{importError}</p>}
        {importPreview && (
          <div className="max-h-96 overflow-y-auto space-y-3">
            <p className="text-sm text-foreground">
              {t('{{count}} row(s) will change.', { count: importPreview.changed_count })}
            </p>
            {importPreview.rows.map((row) => (
              <div key={row.email} className="text-xs border border-border rounded-lg p-2">
                <p className="font-semibold text-foreground">{row.email}</p>
                {Object.entries(row.changes).map(([key, change]) => (
                  <p key={key} className="text-muted-foreground">
                    <span className="font-mono">{key}</span>: {change.old || t('(empty)')} → <span className="text-foreground">{change.new || t('(empty)')}</span>
                  </p>
                ))}
              </div>
            ))}
            {importPreview.unmatched_emails.length > 0 && (
              <div className="text-xs">
                <p className="text-warning font-semibold">
                  {t('{{count}} email(s) not found and will be skipped:', { count: importPreview.unmatched_emails.length })}
                </p>
                <p className="text-muted-foreground">{importPreview.unmatched_emails.join(', ')}</p>
              </div>
            )}
          </div>
        )}
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={closeImportModal}>{t('Cancel')}</Button>
          <Button
            onClick={handleApplyImport}
            disabled={importing || !importPreview || importPreview.changed_count === 0}
          >
            {importing ? t('Applying...') : t('Apply changes')}
          </Button>
        </div>
      </Modal>
    </div>
  );
};

export default UserDataAdmin;
