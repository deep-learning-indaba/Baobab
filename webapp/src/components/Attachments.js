import React, { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { fileService } from '../services/file/file.service';
import { getFileURL } from '../utils/files';
import { resizeImage } from '../utils/imageResize';

var MAX_DIMENSION = 1600;
var JPEG_QUALITY = 0.82;
// Below this, and already within MAX_DIMENSION, re-encoding isn't worth the quality loss.
var SKIP_COMPRESSION_BYTES = 1.5 * 1024 * 1024;
var ACCEPTED_NON_IMAGE_TYPES = ['application/pdf'];

function isAcceptedFile(file) {
  return (!!file.type && file.type.startsWith('image/')) || ACCEPTED_NON_IMAGE_TYPES.indexOf(file.type) !== -1;
}

/**
 * Upload button plus a row of removable chips for a composer's attached
 * images/PDFs. Attachments are never shown as raw markdown to the user -
 * `attachments` is plain {id, name, url, isImage} data that the caller folds
 * into the submitted body via buildBodyMarkdown() only at send time.
 */
function Attachments(props) {
  var attachments = props.attachments || [];
  var onChange = props.onChange, disabled = props.disabled;
  var { t } = useTranslation();
  var inputRef = useRef(null);
  var [uploading, setUploading] = useState(false);
  var [error, setError] = useState('');

  function handleChange(e) {
    var file = e.target.files && e.target.files[0];
    e.target.value = '';
    if (!file) return;

    if (!isAcceptedFile(file)) {
      setError(t('Only images or PDFs can be added.'));
      return;
    }

    var isImage = file.type.startsWith('image/');
    setError('');
    setUploading(true);
    (isImage ? resizeImage(file, { maxDimension: MAX_DIMENSION, quality: JPEG_QUALITY, skipBelowBytes: SKIP_COMPRESSION_BYTES }) : Promise.resolve(file)).then(function (processedFile) {
      return fileService.uploadFile(processedFile);
    }).then(function (response) {
      setUploading(false);
      if (!response.fileId) {
        setError(response.error || t('Upload failed.'));
        return;
      }
      onChange(attachments.concat([{
        id: response.fileId,
        name: file.name,
        url: getFileURL(response.fileId, isImage ? 'inline' : 'attachment', file.name),
        isImage: isImage,
      }]));
    }).catch(function () {
      setUploading(false);
      setError(t('Upload failed.'));
    });
  }

  function removeAttachment(id) {
    onChange(attachments.filter(function (a) { return a.id !== id; }));
  }

  return (
    <div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={function () { inputRef.current && inputRef.current.click(); }}
          disabled={disabled || uploading}
          className="text-muted-foreground hover:text-foreground disabled:opacity-50 px-1"
          title={t('Add attachment')}
          aria-label={t('Add attachment')}
        >
          <i className={uploading ? 'fas fa-spinner fa-spin' : 'fas fa-paperclip'} style={{ fontSize: 15 }} />
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="image/*,application/pdf"
          onChange={handleChange}
          style={{ display: 'none' }}
        />
        {error && <p className="text-xs text-destructive">{error}</p>}
      </div>
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2">
          {attachments.map(function (a) {
            return (
              <div key={a.id} className="relative">
                {a.isImage ? (
                  <img
                    src={a.url}
                    alt={a.name}
                    className="h-14 w-14 object-cover rounded-lg border border-border"
                  />
                ) : (
                  <div
                    className="h-14 w-14 flex flex-col items-center justify-center gap-0.5 rounded-lg border border-border bg-muted/20 px-1 overflow-hidden"
                    title={a.name}
                  >
                    <i className="fas fa-file-pdf text-destructive" style={{ fontSize: 18 }} />
                    <span className="text-[9px] leading-tight text-muted-foreground truncate max-w-full">{a.name}</span>
                  </div>
                )}
                <button
                  type="button"
                  onClick={function () { removeAttachment(a.id); }}
                  className="absolute -top-1.5 -right-1.5 h-5 w-5 flex items-center justify-center rounded-full bg-foreground text-background"
                  aria-label={t('Remove attachment')}
                  title={t('Remove attachment')}
                >
                  <i className="fas fa-times" style={{ fontSize: 10 }} />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default Attachments;
