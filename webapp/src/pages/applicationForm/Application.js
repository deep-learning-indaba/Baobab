import React, { Component } from "react";
import { Redirect } from "react-router-dom";
import { withTranslation } from "react-i18next";
import "./Application.css";
import ApplicationForm from "./components/ApplicationForm"
import FormNotAvailable from "../../components/FormNotAvailable";

class Application extends Component {
  render() {
    const { event, t } = this.props;
    if (event && event.uses_new_forms) {
      if (event.application_form_id) {
        return <Redirect to={"/" + event.key + "/forms/" + event.application_form_id} />;
      }
      return <FormNotAvailable message={t('The application form for this event has not been published yet.')} />;
    }

    return (
      <ApplicationForm
        {...this.props} />
    );
  }
}

export default withTranslation()(Application);
