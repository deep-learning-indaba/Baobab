import React, { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { fileService } from '../services/file/file.service';
import { getInlineFileURL } from '../utils/files';

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
    resizeIfNeeded(file).then(function (processedFile) {
      return fileService.uploadFile(processedFile);
    }).then(function (response) {
      setUploading(false);
      if (!response.fileId) {
        setError(response.error || t('Image upload failed.'));
        return;
      }
      onUpload('![' + file.name + '](' + getInlineFileURL(response.fileId) + ')\n');
    }).catch(function () {
      setUploading(false);
      setError(t('Image upload failed.'));
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
