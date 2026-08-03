import React, { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { fileService } from '../services/file/file.service';
import { getInlineFileURL } from '../utils/files';

/**
 * Small icon button that uploads an image via the generic file-upload
 * endpoint and hands the caller back a markdown image snippet pointing at
 * it, e.g. for inserting into a markdown textarea.
 */
function ImageUploadButton(props) {
  var onUpload = props.onUpload, disabled = props.disabled;
  var { t } = useTranslation();
  var inputRef = useRef(null);
  var [uploading, setUploading] = useState(false);
  var [error, setError] = useState('');

  function handleChange(e) {
    var file = e.target.files && e.target.files[0];
    e.target.value = '';
    if (!file) return;

    if (!file.type || !file.type.startsWith('image/')) {
      setError(t('Only image files can be added.'));
      return;
    }

    setError('');
    setUploading(true);
    fileService.uploadFile(file).then(function (response) {
      setUploading(false);
      if (!response.fileId) {
        setError(response.error || t('Image upload failed.'));
        return;
      }
      onUpload('![' + file.name + '](' + getInlineFileURL(response.fileId) + ')\n');
    });
  }

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={function () { inputRef.current && inputRef.current.click(); }}
        disabled={disabled || uploading}
        className="text-muted-foreground hover:text-foreground disabled:opacity-50 px-1"
        title={t('Add image')}
        aria-label={t('Add image')}
      >
        <i className={uploading ? 'fas fa-spinner fa-spin' : 'fas fa-image'} style={{ fontSize: 15 }} />
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        onChange={handleChange}
        style={{ display: 'none' }}
      />
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}

export default ImageUploadButton;
