import React from 'react';
import icon from '../pages/createApplicationForm/icon.svg';

export const dateFormat = (date) => {
  return new Date(date).toLocaleDateString('en-GB', {
    weekday: 'short',
    month: 'long',
    day: '2-digit',
    year: 'numeric',
    hour: '2-digit'
  })
}

export const TopBar = ({ title, t }) => {
  return (
    <div className="top-bar">
      <div className="icon-title">
        <img src={icon} alt="form" className="icon" />
        <span className="title">{t(title)}</span>
      </div>
    </div>
  );
}