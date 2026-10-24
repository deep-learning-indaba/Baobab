import React from "react";
import { useTranslation } from "react-i18next";

/** Shown where an event's application, review or registration form would be,
 *  when that form has not been set up yet. */
export default function FormNotAvailable({ message, icon = "fa-hourglass-half" }) {
  const { t } = useTranslation();
  return (
    <div className="max-w-xl mx-auto mt-10 rounded-2xl border border-border bg-white p-8 text-center space-y-3">
      <i className={`fas ${icon} text-3xl text-muted-foreground`} />
      <p className="font-heading text-lg font-bold text-foreground">{t('Not yet available')}</p>
      <p className="text-sm text-muted-foreground">{message}</p>
    </div>
  );
}
