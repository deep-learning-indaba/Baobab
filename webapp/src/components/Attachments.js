import React, { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { fileService } from '../services/file/file.service';
import { getFileURL } from '../utils/files';

var MAX_DIMENSION = 1600;
var JPEG_QUALITY = 0.82;
// Below this, and already within MAX_DIMENSION, re-encoding isn't worth the quality loss.
var SKIP_COMPRESSION_BYTES = 1.5 * 1024 * 1024;
// Re-encoding via <canvas> only ever captures a single frame, so animated
// formats must be left untouched rather than "compressed" into a still image.
var UNCOMPRESSIBLE_TYPES = ['image/gif', 'image/svg+xml'];
// Formats browsers commonly can't decode at all (e.g. HEIC straight off an
// iPhone camera). createImageBitmap() rejects fairly reliably for these, but
// this timeout is the real backstop: it guarantees resizeIfNeeded() always
// settles and the upload button never gets stuck spinning.
var RESIZE_TIMEOUT_MS = 8000;
var ACCEPTED_NON_IMAGE_TYPES = ['application/pdf'];

function isAcceptedFile(file) {
  return (!!file.type && file.type.startsWith('image/')) || ACCEPTED_NON_IMAGE_TYPES.indexOf(file.type) !== -1;
}

function renameExtension(name, ext) {
  return (name || 'image').replace(/\.[^./\\]+$/, '') + '.' + ext;
}

/**
 * Downscale and re-encode an image client-side before upload, so a multi-MB,
 * several-thousand-pixel-wide phone photo doesn't get shipped and stored at
 * full size for what's typically a small inline thread image. Falls back to
 * the original file whenever resizing isn't applicable, isn't supported, or
 * fails or stalls for any reason - it must never block the upload.
 */
function resizeIfNeeded(file) {
  if (UNCOMPRESSIBLE_TYPES.indexOf(file.type) !== -1 || typeof createImageBitmap !== 'function') {
    return Promise.resolve(file);
  }

  var resized = createImageBitmap(file).then(function (bitmap) {
    var withinBounds = bitmap.width <= MAX_DIMENSION && bitmap.height <= MAX_DIMENSION;
    if (withinBounds && file.size <= SKIP_COMPRESSION_BYTES) {
      bitmap.close();
      return file;
    }

    var scale = Math.min(1, MAX_DIMENSION / Math.max(bitmap.width, bitmap.height));
    var canvas = document.createElement('canvas');
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close();

    var outputType = file.type === 'image/png' ? 'image/png' : 'image/jpeg';
    return new Promise(function (resolve) {
      canvas.toBlob(function (blob) {
        if (!blob) { resolve(file); return; }
        var name = renameExtension(file.name, outputType === 'image/png' ? 'png' : 'jpg');
        resolve(new File([blob], name, { type: outputType }));
      }, outputType, outputType === 'image/jpeg' ? JPEG_QUALITY : undefined);
    });
  }).catch(function () {
    return file;
  });

  var timeout = new Promise(function (resolve) {
    setTimeout(function () { resolve(file); }, RESIZE_TIMEOUT_MS);
  });

  return Promise.race([resized, timeout]);
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
    (isImage ? resizeIfNeeded(file) : Promise.resolve(file)).then(function (processedFile) {
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
