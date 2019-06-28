import React, { Component } from "react";
import { createColClassName } from "../../../utils/styling/styling";
import validationFields from "../../../utils/validation/validationFields";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import { requiredText, isValidDate } from "../../../utils/validation/rules.js";
import { userService } from "../../../services/user";
import {
  getCounties,
} from "../../../utils/validation/contentHelpers"
import Address from "./Address.js";

const fieldValidations = [
  ruleRunner(validationFields.passportNumber, requiredText),
  ruleRunner(validationFields.fullNameOnPassport, requiredText),
  ruleRunner(validationFields.passportIssuedByAuthority, requiredText),
  ruleRunner(validationFields.passportIssuedByDate, isValidDate)
];
class InvitationLetterForm extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: {
        residence: null,
        nationality: null,
        dateOfBirth: null,
        passportNumber: "",
        fullNameOnPassport: "",
        passportIssuedByAuthority: "",
        bringingAPoster: false
      },
      submitted: false,
      loading: false,
      showWorkAddress: false,
      errors: []
    };
  }

  componentWillMount() {
    getCounties.then(result => {
      this.setState({
        countryOptions: this.checkOptionsList(result[2]),
      });
    });

    userService.get().then(result => {
      var date = result.user_dateOfBirth;
      if (date) date = date.split("T")[0];
      this.setState({
        user: {
          nationality: result.nationality_country_id,
          residence: result.residence_country_id,
          dateOfBirth: date,
        }
      });
    });
  }
  handleChange = field => {
    return event => {
      this.setState(
        {
          user: {
            ...this.state.user,
            [field.name]: event.target.value
          }
        },
        function () {
          let errorsForm = run(this.state.user, fieldValidations);
          this.setState({ errors: { $set: errorsForm } });
        }
      );
    };
  };
  validateForm() {
    return (
      this.state.user.passportNumber.length > 0 &&
      this.state.user.fullNameOnPassport.length > 0 &&
      this.state.user.passportIssuedByAuthority.length > 0
    );
  }
  handleSubmit = event => {
    event.preventDefault();
    this.setState({ submitted: true, showErrors: true });
  };
  toggleWork = () => {
    let currentShowAddressState = this.state.showWorkAddress;
    this.setState({ showWorkAddress: !currentShowAddressState });
  };
  toggleBringingAPoster = () => {
    let currentBringingAPoster = this.state.user.bringingAPoster;
    this.setState({
      user: { ...this.state.user, bringingAPoster: !currentBringingAPoster }
    });
  };
  render() {
    const {
      passportNumber,
      fullNameOnPassport,
      passportIssuedByDate,
      passportIssuedByAuthority,
      nationality,
      residence,
      dateOfBirth,
      workStreet1,
      workStreet2,
      workCity,
      workPostalCode,
      workCountry,
      residentialStreet1,
      residentialStreet2,
      residentialCity,
      residentialPostalCode,
      residentialCountry,
      bringingAPoster
    } = this.state.user;

    const { loading, errors, showErrors, error, showWorkAddress } = this.state;

    const passportDetailsStyle = createColClassName(12, 2, 3, 3);
    const nationResidenceDetailsStyle = createColClassName(12, 3, 4, 4);
    const checkboxStyle = createColClassName(12, 4, 6, 6);
    return (
      <div className="InvitationLetter">
        <form onSubmit={this.handleSubmit}>
          <p className="h5 text-center mb-4">Invitation Letter</p>
          <div class="row">
            <div class={passportDetailsStyle}>
              <FormTextBox
                id={validationFields.fullNameOnPassport.name}
                type="text"
                placeholder={validationFields.fullNameOnPassport.display}
                onChange={this.handleChange(
                  validationFields.fullNameOnPassport
                )}
                value={fullNameOnPassport}
                label={validationFields.fullNameOnPassport.display}
                description={validationFields.fullNameOnPassport.description}
              />
            </div>
            <div class={passportDetailsStyle}>
              <FormTextBox
                id={validationFields.passportNumber.name}
                type="text"
                placeholder={validationFields.passportNumber.display}
                onChange={this.handleChange(validationFields.passportNumber)}
                value={passportNumber}
                label={validationFields.passportNumber.display}
              />
            </div>

            <div class={passportDetailsStyle}>
              <FormTextBox
                id={validationFields.passportIssuedByDate.name}
                type="date"
                placeholder={validationFields.passportIssuedByDate.display}
                onChange={this.handleChange(
                  validationFields.passportIssuedByDate
                )}
                value={passportIssuedByDate}
                label={validationFields.passportIssuedByDate.display}
              />
            </div>
            <div class={passportDetailsStyle}>
              <FormTextBox
                id={validationFields.passportIssuedByAuthority.name}
                type="text"
                placeholder={validationFields.passportIssuedByAuthority.display}
                onChange={this.handleChange(
                  validationFields.passportIssuedByAuthority
                )}
                value={passportIssuedByAuthority}
                label={validationFields.passportIssuedByAuthority.display}
              />
            </div>
          </div>
          <div class="row">
            <div class={checkboxStyle}>
              <label>
                {"Will you be presenting a poster ? "}
                <input
                  name="bringingPoster"
                  type="checkbox"
                  checked={bringingAPoster}
                  onChange={this.toggleBringingAPoster}
                />
              </label>
            </div>
            <div class={checkboxStyle}>
              <label>
                {"Are you currently employed ? "}
                <input
                  name="showWorkAddress"
                  type="checkbox"
                  checked={showWorkAddress}
                  onChange={this.toggleWork}
                />
              </label>
            </div>
          </div>
          <div class="row">
            <Address
              onChange={this.handleChange}
              streetAddress1={validationFields.residentialStreet1}
              streetAddress2={validationFields.residentialStreet2}
              city={validationFields.residentialCity}
              postalCode={validationFields.residentialPostalCode}
              country={validationFields.residentialCountry}
              streetAddress1Value={residentialStreet1}
              streetAddress2Value={residentialStreet2}
              cityValue={residentialCity}
              postalCodeValue={residentialPostalCode}
              countryValue={residentialCountry}
            />
            {showWorkAddress && (
              <Address
                onChange={this.handleChange}
                streetAddress1={validationFields.workStreet1}
                streetAddress2={validationFields.workStreet2}
                city={validationFields.workCity}
                postalCode={validationFields.workPostalCode}
                country={validationFields.workCountry}
                streetAddress1Value={workStreet1}
                streetAddress2Value={workStreet2}
                cityValue={workCity}
                postalCodeValue={workPostalCode}
                countryValue={workCountry}
              />
            )}
          </div>

          <p>
            We have the following values required for your invitation from your
            user profile. Please go to the user page if you need to update them.
          </p>
          <div class="row">
            <div class={nationResidenceDetailsStyle}>
              <FormSelect
                options={this.state.countryOptions}
                id={validationFields.nationality.name}
                placeholder={validationFields.nationality.display}
                onChange={this.handleChangeDropdown}
                value={nationality}
                label={validationFields.nationality.display}
              />
            </div>
            <div class={nationResidenceDetailsStyle}>
              <FormSelect
                options={this.state.countryOptions}
                id={validationFields.residence.name}
                placeholder={validationFields.residence.display}
                onChange={this.handleChangeDropdown}
                value={residence}
                label={validationFields.residence.display}
              />
            </div>

            <div class={nationResidenceDetailsStyle}>
              <FormTextBox
                id={validationFields.dateOfBirth.name}
                type="date"
                placeholder={validationFields.dateOfBirth.display}
                onChange={this.handleChange(validationFields.dateOfBirth)}
                value={dateOfBirth}
                label={validationFields.dateOfBirth.display}
              />
            </div>
          </div>
          <button
            type="submit"
            class="btn btn-primary"
            disabled={!this.validateForm() || loading}
          >
            {loading && (
              <span
                class="spinner-grow spinner-grow-sm"
                role="status"
                aria-hidden="true"
              />
            )}
            Request Invitation Letter
          </button>
          {errors && errors.$set && showErrors && this.getErrorMessages(errors)}
          {error && <div class="alert alert-danger">{error}</div>}
        </form>
      </div>
    );
  }
}

export default InvitationLetterForm;
