import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

/**
 * Markdown `img` renderer that shows a capped-size thumbnail (sized via the
 * .discussion-thumb CSS class) and opens a full-size view in a lightbox on
 * click. Meant to be passed to MarkdownRenderer as `components={{ img: LightboxImage }}`.
 */
function LightboxImage({ src, alt }) {
  var [expanded, setExpanded] = useState(false);
  var { t } = useTranslation();

  return (
    <React.Fragment>
      <img
        src={src}
        alt={alt}
        className="discussion-thumb"
        onClick={function () { setExpanded(true); }}
      />
      {expanded && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80"
          onClick={function () { setExpanded(false); }}
        >
          <img
            src={src}
            alt={alt}
            className="max-w-full max-h-full rounded-lg"
            onClick={function (e) { e.stopPropagation(); }}
          />
          <button
            type="button"
            onClick={function () { setExpanded(false); }}
            className="absolute top-4 right-4 h-9 w-9 flex items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20"
            aria-label={t('Close')}
            title={t('Close')}
          >
            <i className="fas fa-times" style={{ fontSize: 16 }} />
          </button>
        </div>
      )}
    </React.Fragment>
  );
}

export default LightboxImage;
