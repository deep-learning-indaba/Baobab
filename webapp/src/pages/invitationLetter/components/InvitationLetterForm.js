// TOOD: ADD TRANSLATION
import React, { Component } from "react";
import { createColClassName } from "../../../utils/styling/styling";
import validationFields from "../../../utils/validation/validationFields";
import FormTextBox from "../../../components/form/FormTextBox";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import {
  requiredText,
  isValidDate,
  requiredDropdown
} from "../../../utils/validation/rules.js";
import FormSelect from "../../../components/form/FormSelect";
import { getCountries } from "../../../utils/validation/contentHelpers";
import Address from "./Address.js";
import { registrationService } from "../../../services/registration";
import Loading from "../../../components/Loading";
import { withRouter } from "react-router";
import { withTranslation } from 'react-i18next';

const fieldValidations = [
  ruleRunner(validationFields.passportNumber, requiredText),
  ruleRunner(validationFields.fullNameOnPassport, requiredText),
  ruleRunner(validationFields.passportIssuedByAuthority, requiredText),
  ruleRunner(validationFields.passportExpiryDate, isValidDate),
  ruleRunner(validationFields.residentialStreet1, requiredText),
  ruleRunner(validationFields.residentialCity, requiredText),
  ruleRunner(validationFields.residentialPostalCode, requiredText),
  ruleRunner(validationFields.residentialCountry, requiredDropdown),
  ruleRunner(validationFields.letterAddressedTo, requiredText)
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
      loading: false,
      loadingPage: true,
      showWorkAddress: false,
      errors: [],
      available: false,
      error: null
    };
  }

  checkOptionsList(optionsList) {
    if (Array.isArray(optionsList)) {
      return optionsList.map(c => ({
        value: c.label, 
        label: c.label
      }));
    } else return [];
  }

  getContentValue(options, value) {
    if (options && options.filter) {
      return options.filter(option => {
        return option.value === value;
      });
    } else return null;
  }

  componentWillMount() {
    Promise.all([
      getCountries,
      registrationService.invitationLetterAvailable(this.props.event ? this.props.event.id : 0)
    ]).then(([countriesResult, availableResponse]) => {
      this.setState({
        countryOptions: this.checkOptionsList(countriesResult),
        loadingPage: false,
        available: availableResponse.data.available
      });
    }).catch(error => {
      this.setState({
        loadingPage: false,
        error: error.response && error.response.data
          ? error.response.data.message
          : error.message
      });
    });
  }
  handleChangeDropdown = (name, dropdown) => {
    this.setState(
      {
        user: {
          ...this.state.user,
          [name]: dropdown.value
        }
      },
      function() {
        let errorsForm = run(this.state.user, fieldValidations);
        this.setState({ errors: { $set: errorsForm } });
      }
    );
  };
  handleChange = field => {
    return event => {
      this.setState(
        {
          user: {
            ...this.state.user,
            // React datepicker component's onChange contains the value and not event.target.value
            [field.name]: event && event.target ? event.target.value : event
          }
        },
        function() {
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
      this.state.user.passportIssuedByAuthority.length > 0 &&
      this.state.user.residentialStreet1 &&
      this.state.user.residentialStreet1.length > 0 &&
      this.state.user.residentialCity &&
      this.state.user.residentialCity.length > 0 &&
      this.state.user.residentialPostalCode &&
      this.state.user.residentialPostalCode.length > 0 &&
      this.state.user.residentialCountry &&
      this.state.user.letterAddressedTo.length > 0 &&
      this.state.user.residence &&
      this.state.user.nationality &&
      this.state.user.dateOfBirth != null
    );
  }
  convertAddressField = (street1, street2, city, postalCode, country) => {
    let newline = "\n";
    let fullAddress = "";
    if (street2)
      fullAddress = fullAddress.concat(
        street1,
        newline,
        street2,
        newline,
        city,
        newline,
        postalCode,
        newline,
        country
      );
    else
      fullAddress = fullAddress.concat(
        street1,
        newline,
        city,
        newline,
        postalCode,
        newline,
        country
      );

    return fullAddress;
  };
  handleSubmit = event => {
    if (
      this.state.errors &&
      this.state.errors.$set &&
      this.state.errors.$set.length > 0
    )
      return;

    event.preventDefault();
    const {
      workStreet1,
      workStreet2,
      workCity,
      workPostalCode,
      workCountry,
      residentialStreet1,
      residentialStreet2,
      residentialCity,
      residentialPostalCode,
      residentialCountry
    } = this.state.user;
    let workFullAddress = null;
    const residentialCountryValue = this.getContentValue(
      this.state.countryOptions,
      residentialCountry
    );
    if (this.state.showWorkAddress === true) {
      const workCountryValue = this.getContentValue(
        this.state.countryOptions,
        workCountry
      );
      workFullAddress = this.convertAddressField(
        workStreet1,
        workStreet2,
        workCity,
        workPostalCode,
        workCountryValue
      );
    }

    let residentialFullAddress = this.convertAddressField(
      residentialStreet1,
      residentialStreet2,
      residentialCity,
      residentialPostalCode,
      residentialCountryValue
    );

    this.setState(
      {
        user: {
          ...this.state.user,
          workFullAddress: workFullAddress,
          residentialFullAddress: residentialFullAddress
        }
      },
      () => {
        this.setState({ loading: true });
        registrationService
          .requestInvitationLetter(
            this.state.user,
            this.props.event ? this.props.event.id : 0
          )
          .then(
            response => {
              this.setState({
                loading: false,
                invitationLetterId:
                  response && response.data
                    ? response.data.invitation_letter_request_id
                    : null,
                error: response.error
              });
              if (response && response.data && response.data.invitation_letter_request_id) {
                this.setState({
                  user: {
                    residence: null,
                    nationality: null,
                    dateOfBirth: null,
                    passportNumber: "",
                    fullNameOnPassport: "",
                    passportIssuedByAuthority: "",
                    bringingAPoster: false
                  }
                });
              }
            },
            error =>
              this.setState({
                error:
                  error.response && error.response.data
                    ? error.response.data.message
                    : error.message,
                loading: false
              })
          );
        this.setState({ showErrors: true });
      }
    );
  };

  toggleWork = () => {
    let currentShowAddressState = this.state.showWorkAddress;
    this.setState({ showWorkAddress: !currentShowAddressState });
  };

  toggleBringingAPoster = () => {
    let currentBringingAPoster = this.state.user.bringingAPoster;
    this.setState({
      user: {
        ...this.state.user,
        bringingAPoster: !currentBringingAPoster
      }
    });
  };

  getErrorMessages = errors => {
    let errorMessages = [];
    if (errors.$set === null) return;

    let arr = errors.$set;

    for (let i = 0; i < arr.length; i++) {
      errorMessages.push(
        <div className={"alert alert-danger alert-container"}>
          {Object.values(arr[i])}
        </div>
      );
    }
    return errorMessages;
  };

  render() {
    const {
      passportNumber,
      fullNameOnPassport,
      passportExpiryDate,
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
      letterAddressedTo
    } = this.state.user;

    const {
      loadingPage,
      loading,
      errors,
      showErrors,
      error,
      showWorkAddress,
      countryOptions,
      available
    } = this.state;

    if (loadingPage) {
      return <Loading />;
    }

    if (!available) {
      return <div className="alert alert-warning">{this.props.t("Invitation letter is not yet available, please check again at a later date.")}</div>;
    }

    const nationalityValue = this.getContentValue(
      this.state.countryOptions,
      nationality
    );

    const residenceValue = this.getContentValue(
      this.state.countryOptions,
      residence
    );

    const passportDetailsStyleLine = createColClassName(12, 3, 4, 4);
    const nationResidenceDetailsStyle = createColClassName(12, 3, 4, 4);
    return (
      <div className="InvitationLetter">
        <form onSubmit={this.handleSubmit}>
          <p className="h5 text-center mb-4">Invitation Letter</p>

          <div className="row">
            <div className={passportDetailsStyleLine}>
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

            <div className={passportDetailsStyleLine}>
              <FormTextBox
                id={validationFields.passportNumber.name}
                type="text"
                placeholder={validationFields.passportNumber.display}
                onChange={this.handleChange(validationFields.passportNumber)}
                value={passportNumber}
                label={validationFields.passportNumber.display}
              />
            </div>

            <div class={passportDetailsStyleLine}>
              <FormTextBox
                id={validationFields.passportExpiryDate.name}
                type="date"
                placeholder={validationFields.passportExpiryDate.display}
                onChange={this.handleChange(
                  validationFields.passportExpiryDate
                )}
                value={passportExpiryDate}
                label={validationFields.passportExpiryDate.display}
              />
            </div>
          </div>

          <div className="row">
            <div className={passportDetailsStyleLine}>
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

            <div className={passportDetailsStyleLine}>
              <FormTextBox
                id={validationFields.letterAddressedTo.name}
                type="text"
                placeholder={validationFields.letterAddressedTo.display}
                onChange={this.handleChange(validationFields.letterAddressedTo)}
                value={letterAddressedTo}
                label={validationFields.letterAddressedTo.display}
                description={validationFields.letterAddressedTo.description}
              />
            </div>

            <div className={passportDetailsStyleLine}>
              <div id="labelWorkAddress">
                {"Are you currently employed ? "}
                <input
                  name="showWorkAddress"
                  type="checkbox"
                  checked={showWorkAddress}
                  onChange={this.toggleWork}
                />
              </div>
            </div>
          </div>

          <div className="row">
            <Address
              onChange={this.handleChange}
              handleChangeDropdown={this.handleChangeDropdown}
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
              countryOptions={countryOptions}
            />

            {showWorkAddress && (
              <Address
                onChange={this.handleChange}
                handleChangeDropdown={this.handleChangeDropdown}
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
                countryOptions={countryOptions}
              />
            )}
          </div>

          <div class="row">
            <div class={nationResidenceDetailsStyle}>
              <FormSelect
                options={countryOptions}
                id={validationFields.nationality.name}
                placeholder={validationFields.nationality.display}
                value={nationalityValue}
                label={validationFields.nationality.display}
                onChange={this.handleChangeDropdown}
              />
            </div>

            <div class={nationResidenceDetailsStyle}>
              <FormSelect
                options={countryOptions}
                id={validationFields.residence.name}
                placeholder={validationFields.residence.display}
                value={residenceValue}
                label={validationFields.residence.display}
                onChange={this.handleChangeDropdown}
              />
            </div>

            <div class={nationResidenceDetailsStyle}>
              <FormTextBox
                id={validationFields.dateOfBirth.name}
                type="date"
                placeholder={validationFields.dateOfBirth.display}
                value={dateOfBirth}
                label={validationFields.dateOfBirth.display}
                onChange={this.handleChange(validationFields.dateOfBirth)}
              />
            </div>
          </div>

          <button
            type="submit"
            class="btn btn-primary"
            id="btn-invitationLetter-submit"
            disabled={!this.validateForm() || loading}
          >
            {loading && (
              <span
                className="spinner-grow spinner-grow-sm"
                role="status"
                aria-hidden="true"
              />
            )}
            Request Invitation Letter
          </button>

          {errors && errors.$set && showErrors && this.getErrorMessages(errors)}

          {error && (
            <div
              class="alert alert-danger alert-container"
              id="alert-invitation-letter-failure"
            >
              {error}
            </div>
          )}

          {this.state.invitationLetterId && (
            <div
              class="alert alert-success alert-container"
              id="alert-invitation-letter-success"
            >
              Thank you, your invitation letter will be sent to your email address.
            </div>
          )}
        </form>
      </div>
    );
  }
}

export default withRouter(withTranslation()(InvitationLetterForm));
