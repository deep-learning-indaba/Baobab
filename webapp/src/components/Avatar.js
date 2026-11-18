import React, { useState, useEffect } from 'react';
import { getImage } from '../utils/images';

var SIZE_CLASSES = {
  sm: 'w-8 h-8 text-xs',
  md: 'w-12 h-12 text-lg',
  lg: 'w-20 h-20 text-2xl',
  xl: 'w-24 h-24 text-3xl',
};

function Avatar({ photoUrl, firstname, lastname, size = 'md', alt = '', className = '' }) {
  var [failed, setFailed] = useState(false);

  useEffect(function () { setFailed(false); }, [photoUrl]);

  var sz = SIZE_CLASSES[size] || SIZE_CLASSES.md;
  var src = getImage(photoUrl);

  if (src && !failed) {
    return (
      <img
        src={src}
        alt={alt}
        onError={function () { setFailed(true); }}
        className={sz + ' rounded-full object-cover flex-shrink-0 ' + className}
      />
    );
  }

  var initials = (firstname || '?')[0].toUpperCase() + (lastname || '?')[0].toUpperCase();
  return (
    <div
      className={sz + ' rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary flex-shrink-0 ' + className}
      role={alt ? 'img' : undefined}
      aria-label={alt || undefined}
      aria-hidden={alt ? undefined : true}
    >
      {initials}
    </div>
  );
}

export default Avatar;
