import React, { Component } from "react";
import { Redirect } from "react-router-dom";
import { withTranslation } from "react-i18next";
import FormNotAvailable from "../../components/FormNotAvailable";
import "./Registration.css";
import RegistrationComponent from "./components/RegistrationComponent"
import GuestRegistrationComponent from "./components/GuestRegistrationComponent"
import { invitedGuestServices } from '../../services/invitedGuests/invitedGuests.service';

class Registration extends Component {

  constructor(props) {
    super(props);
    this.state = {
      GuestRegistration: null
    }
  }

  componentDidMount() {
    invitedGuestServices.determineIfInvitedGuest(
      this.props.event ? this.props.event.id : 0).then(
        response => {
          if (response.statusCode === "200") {
            this.setState({
              GuestRegistration: true
            });
          }
          else if (response.statusCode === "404") {
            this.setState({
              GuestRegistration: false
            });
          }
        })
  }
  render() {
    const { event, t } = this.props;
    if (event && !event.is_registration_open) {
      return <div className="alert alert-danger">{t('Registration is now closed')}</div>
    }

    if (event && event.uses_new_forms) {
      if (event.registration_form_id) {
        return <Redirect to={"/" + event.key + "/forms/" + event.registration_form_id} />;
      }
      return <FormNotAvailable message={t('The registration form for this event has not been published yet.')} />;
    }
    return (
      <div>
        {this.state.GuestRegistration === true ?
          <GuestRegistrationComponent
            {...this.props}>
          </GuestRegistrationComponent> : this.state.GuestRegistration === false ?
            <RegistrationComponent
              {...this.props}>
            </RegistrationComponent> : ""}
      </div>
    );
  }
}

export default withTranslation()(Registration);
