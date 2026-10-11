import React, { Component } from "react";
import { Link } from "react-router-dom";
import { withTranslation } from "react-i18next";
import "./RegistrationAdmin.css";
import RegistrationAdminComponent from "./components/RegistrationAdminComponent.js"

class RegistrationAdmin extends Component {

  render() {
    const { event, t } = this.props;
    // New-system registrations are confirmed by payment, not by hand.
    if (event && event.uses_new_forms) {
      return (
        <div className="max-w-xl mx-auto mt-10 rounded-2xl border border-border bg-white p-8 space-y-3 text-left">
          <h1 className="font-heading text-lg font-bold text-foreground">{t('Registration Admin')}</h1>
          <p className="text-sm text-muted-foreground">
            {t('Registrations are confirmed automatically once the attendee’s offer is paid, or straight away when no payment is required. Invited guests are confirmed when they register.')}
          </p>
          <div className="flex flex-wrap gap-4 text-sm font-semibold">
            <Link to={`/${event.key}/invoices-admin`} className="text-action hover:underline">{t('Invoices')}</Link>
            {event.registration_form_id && (
              <Link to={`/${event.key}/form-responses/${event.registration_form_id}`} className="text-action hover:underline">
                {t('Registration responses')}
              </Link>
            )}
          </div>
        </div>
      );
    }

    return (
      <RegistrationAdminComponent
        {...this.props}>
      </RegistrationAdminComponent>
    );
  }
}

export default withTranslation()(RegistrationAdmin);
