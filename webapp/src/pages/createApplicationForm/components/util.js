import React from 'react';

export const option = ({ value, t, label: l, faClass }) => {
  const label = faClass ? <div>
    <div className='dropdown-text'>
      <i className={faClass}></i>
    </div>
    {t(l)}
  </div>
  : t(l);
  return {
    label,
    value
  }
}

export const langObject = (langs, value) => langs && langs.reduce((obj, item) => Object.assign(obj,
  {
    [item.code]: value
  }
), {});
