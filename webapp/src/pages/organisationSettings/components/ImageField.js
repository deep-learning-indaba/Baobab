import React, { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { fileService } from '../../../services/file/file.service';
import { getImage } from '../../../utils/images';

/** A thumbnail with Upload and (for optional images) Remove actions. */
const ImageField = ({ id, label, hint, value, onChange, required, error }) => {
  const { t } = useTranslation();
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const url = getImage(value);

  const handleFile = (e) => {
    const file = e.target.files && e.target.files[0];
    e.target.value = '';
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setUploadError(t('Only images can be uploaded here.'));
      return;
    }
    setUploadError('');
    setUploading(true);
    fileService.uploadFile(file).then((response) => {
      setUploading(false);
      if (response.fileId) onChange(response.fileId);
      else setUploadError(response.error || t('Upload failed.'));
    });
  };

  return (
    <div className="text-sm">
      <span id={`${id}-label`} className="font-medium text-foreground">{label}</span>
      <div className="mt-1 flex items-center gap-3">
        <div className="h-12 w-12 shrink-0 rounded-lg border border-border bg-surface-low flex items-center justify-center overflow-hidden">
          {url
            ? <img src={url} alt={t('{{field}} preview', { field: label })} className="max-h-full max-w-full object-contain" />
            : <span className="text-[10px] text-muted-foreground">{t('Not set')}</span>}
        </div>
        <input
          ref={inputRef}
          id={id}
          type="file"
          accept="image/*"
          aria-labelledby={`${id}-label`}
          className="sr-only"
          onChange={handleFile}
        />
        <button type="button" disabled={uploading}
          onClick={() => inputRef.current.click()}
          className="rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-surface-low cursor-pointer disabled:opacity-50">
          {uploading ? t('Uploading...') : t('Upload')}
        </button>
        {!required && value && (
          <button type="button" className="text-xs text-action hover:underline cursor-pointer"
            onClick={() => onChange('')}>
            {t('Remove')}
          </button>
        )}
      </div>
      {(uploadError || error) && <span className="block text-xs text-error mt-1">{uploadError || error}</span>}
      {hint && <span className="block text-xs text-muted-foreground mt-1">{hint}</span>}
    </div>
  );
};

export default ImageField;
