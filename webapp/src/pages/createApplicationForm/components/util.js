import React from 'react';

export const option = props => {
  const { value, t } = props;
  const label = <div>
    <div className='dropdown-text'>
      <i className={props.faClass}></i>
    </div>
    {t(props.label)}
  </div>
  return {
    label,
    value
  }
}