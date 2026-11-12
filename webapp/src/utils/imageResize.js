// Re-encoding via <canvas> only ever captures a single frame, so animated
// formats must be left untouched rather than "compressed" into a still image.
var UNCOMPRESSIBLE_TYPES = ['image/gif', 'image/svg+xml'];

function renameExtension(name, ext) {
  return (name || 'image').replace(/\.[^./\\]+$/, '') + '.' + ext;
}

/**
 * Downscale and re-encode an image client-side before upload.
 *
 * Options:
 *  - maxDimension: longest side of the output, in px (never upscales).
 *  - squareCrop: centre-crop to a square, always output JPEG on a white
 *    background, and always re-encode regardless of size.
 *  - quality: JPEG quality (0-1).
 *  - skipBelowBytes: return the original when it is already within
 *    maxDimension and no larger than this (ignored with squareCrop).
 *  - timeoutMs: give up after this long. Formats browsers can't decode (e.g.
 *    HEIC) normally reject quickly, but the timeout guarantees the promise
 *    always settles.
 *  - outputType: force 'image/jpeg' or 'image/png'. Defaults to PNG for PNG
 *    input and JPEG otherwise.
 *  - rejectOnFailure: reject instead of resolving with the original file when
 *    the image can't be processed (including GIF/SVG and non-image types).
 *    Without it, the original file is returned so an upload is never blocked.
 */
export function resizeImage(file, options) {
  var opts = options || {};
  var maxDimension = opts.maxDimension;
  var squareCrop = !!opts.squareCrop;
  var quality = opts.quality === undefined ? 0.82 : opts.quality;
  var skipBelowBytes = opts.skipBelowBytes || 0;
  var timeoutMs = opts.timeoutMs === undefined ? 8000 : opts.timeoutMs;
  var rejectOnFailure = !!opts.rejectOnFailure;

  function fail(message) {
    return rejectOnFailure ? Promise.reject(new Error(message)) : Promise.resolve(file);
  }

  var isImage = !!file.type && file.type.startsWith('image/');
  if (UNCOMPRESSIBLE_TYPES.indexOf(file.type) !== -1 || (rejectOnFailure && !isImage)) {
    return fail('Unsupported image type');
  }
  if (typeof createImageBitmap !== 'function') {
    return fail('Image processing is not supported');
  }

  var outputType = squareCrop
    ? 'image/jpeg'
    : (opts.outputType || (file.type === 'image/png' ? 'image/png' : 'image/jpeg'));

  var resized = createImageBitmap(file).then(function (bitmap) {
    var longest = Math.max(bitmap.width, bitmap.height);
    var withinBounds = !maxDimension || longest <= maxDimension;
    if (!squareCrop && withinBounds && file.size <= skipBelowBytes) {
      bitmap.close();
      return file;
    }

    var sx = 0, sy = 0, sw = bitmap.width, sh = bitmap.height;
    if (squareCrop) {
      var side = Math.min(bitmap.width, bitmap.height);
      sx = Math.round((bitmap.width - side) / 2);
      sy = Math.round((bitmap.height - side) / 2);
      sw = side;
      sh = side;
    }

    var scale = maxDimension ? Math.min(1, maxDimension / Math.max(sw, sh)) : 1;
    var canvas = document.createElement('canvas');
    canvas.width = Math.round(sw * scale);
    canvas.height = Math.round(sh * scale);
    var ctx = canvas.getContext('2d');
    if (outputType === 'image/jpeg' && squareCrop) {
      // JPEG has no alpha channel; transparent pixels would otherwise turn black.
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
    ctx.drawImage(bitmap, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);
    bitmap.close();

    return new Promise(function (resolve, reject) {
      canvas.toBlob(function (blob) {
        if (!blob) {
          if (rejectOnFailure) reject(new Error('Could not encode image'));
          else resolve(file);
          return;
        }
        var name = renameExtension(file.name, outputType === 'image/png' ? 'png' : 'jpg');
        resolve(new File([blob], name, { type: outputType }));
      }, outputType, outputType === 'image/jpeg' ? quality : undefined);
    });
  }).catch(function (err) {
    return fail(err && err.message ? err.message : 'Could not decode image');
  });

  var timeout = new Promise(function (resolve, reject) {
    setTimeout(function () {
      if (rejectOnFailure) reject(new Error('Image processing timed out'));
      else resolve(file);
    }, timeoutMs);
  });

  return Promise.race([resized, timeout]);
}
