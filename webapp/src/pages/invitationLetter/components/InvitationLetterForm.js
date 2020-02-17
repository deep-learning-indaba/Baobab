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
import { userService } from "../../../services/user";
import { getCounties } from "../../../utils/validation/contentHelpers";
import Address from "./Address.js";
import { registrationService } from "../../../services/registration";

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
      showWorkAddress: false,
      errors: []
    };
  }

  checkOptionsList(optionsList) {
    if (Array.isArray(optionsList)) {
      return optionsList;
    } else return [];
  }
  getContentValue(options, value) {
    if (options && options.filter) {
      let optionsObject = options.filter(option => {
        return option.value === value;
      });
      if (optionsObject && optionsObject[0])
        return optionsObject[0].label;
    } else return null;
  }

  componentWillMount() {
    getCounties.then(result => {
      this.setState({
        countryOptions: this.checkOptionsList(result)
      });
    });

    userService.get().then(result => {
      var date = result.user_dateOfBirth;
      if (date) date = date.split("T")[0];
      this.setState({
        user: {
          ...this.state.user,
          nationality: result.nationality_country_id,
          residence: result.residence_country_id,
          dateOfBirth: date
        }
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
      function () {
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
      this.state.user.passportIssuedByAuthority.length > 0 &&
      this.state.user.residentialStreet1 &&
      this.state.user.residentialStreet1.length > 0 &&
      this.state.user.residentialCity &&
      this.state.user.residentialCity.length > 0 &&
      this.state.user.residentialPostalCode &&
      this.state.user.residentialPostalCode.length > 0 &&
      this.state.user.residentialCountry &&
      this.state.user.letterAddressedTo.length > 0
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
        registrationService.requestInvitationLetter(
          this.state.user,
          this.props.event ?
            this.props.event.id : 0).then(
              response => {
                this.setState({
                  loading: false,
                  invitationLetterId:
                    response && response.data
                      ? response.data.invitation_letter_request_id
                      : null,
                  error: response.error
                });
              },
              error => this.setState({
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
    if (errors.$set === null)
      return;

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
      loading,
      errors,
      showErrors,
      error,
      showWorkAddress,
      countryOptions
    } = this.state;

    const nationalityValue = this.getContentValue(
      this.state.countryOptions,
      nationality);

    const residenceValue = this.getContentValue(
      this.state.countryOptions,
      residence);

    const passportDetailsStyleLine = createColClassName(12, 3, 4, 4);
    const nationResidenceDetailsStyle = createColClassName(12, 3, 4, 4);
    return (
      <div className="InvitationLetter">
        <form onSubmit={this.handleSubmit}>
          <p className="h5 text-center mb-4">Invitation Letter</p>

          <div class="row">
            <div class={passportDetailsStyleLine}>
              <FormTextBox
                id={validationFields.fullNameOnPassport.name}
                type="text"
                placeholder={validationFields.fullNameOnPassport.display}

                onChange={this.handleChange(
                  validationFields.fullNameOnPassport)}
                value={fullNameOnPassport}
                label={validationFields.fullNameOnPassport.display}
                description={validationFields.fullNameOnPassport.description} />
            </div>

            <div class={passportDetailsStyleLine}>
              <FormTextBox
                id={validationFields.passportNumber.name}
                type="text"
                placeholder={validationFields.passportNumber.display}
                onChange={this.handleChange(validationFields.passportNumber)}
                value={passportNumber}
                label={validationFields.passportNumber.display} />
            </div>

            <div class={passportDetailsStyleLine}>
              <FormTextBox
                id={validationFields.passportExpiryDate.name}
                type="date"
                placeholder={validationFields.passportExpiryDate.display}
                onChange={this.handleChange(
                  validationFields.passportExpiryDate)}
                value={passportExpiryDate}
                label={validationFields.passportExpiryDate.display} />
            </div>
          </div>

          <div class="row">
            <div class={passportDetailsStyleLine}>
              <FormTextBox
                id={validationFields.passportIssuedByAuthority.name}
                type="text"
                placeholder={validationFields.passportIssuedByAuthority.display}
                onChange={this.handleChange(
                  validationFields.passportIssuedByAuthority)}
                value={passportIssuedByAuthority}
                label={validationFields.passportIssuedByAuthority.display} />
            </div>

            <div class={passportDetailsStyleLine}>
              <FormTextBox
                id={validationFields.letterAddressedTo.name}
                type="text"
                placeholder={validationFields.letterAddressedTo.display}
                onChange={this.handleChange(validationFields.letterAddressedTo)}
                value={letterAddressedTo}
                label={validationFields.letterAddressedTo.display}
                description={validationFields.letterAddressedTo.description} />
            </div>

            <div class={passportDetailsStyleLine}>
              <div id="labelWorkAddress">
                {"Are you currently employed ? "}
                <input
                  name="showWorkAddress"
                  type="checkbox"
                  checked={showWorkAddress}
                  onChange={this.toggleWork} />
              </div>
            </div>
          </div>

          <div class="row">
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
              countryOptions={countryOptions} />

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

          <p>
            We have the following values required for your invitation from your
            user profile. Please go to the user profile page if you need to
            update them.
          </p>
          <div class="row">

            <div class={nationResidenceDetailsStyle}>
              <FormTextBox
                type="text"
                id={validationFields.nationality.name}
                placeholder={validationFields.nationality.display}
                value={nationalityValue}
                label={validationFields.nationality.display} />
            </div>

            <div class={nationResidenceDetailsStyle}>
              <FormTextBox
                type="text"
                id={validationFields.residence.name}
                placeholder={validationFields.residence.display}
                value={residenceValue}
                label={validationFields.residence.display} />
            </div>

            <div class={nationResidenceDetailsStyle}>
              <FormTextBox
                id={validationFields.dateOfBirth.name}
                type="date"
                placeholder={validationFields.dateOfBirth.display}
                value={dateOfBirth}
                label={validationFields.dateOfBirth.display} />
            </div>
          </div>

          <button
            type="submit"
            class="btn btn-primary"
            disabled={!this.validateForm() || loading}>

            {loading && (
              <span
                class="spinner-grow spinner-grow-sm"
                role="status"
                aria-hidden="true" />)}
            Request Invitation Letter
          </button>

          {errors &&
            errors.$set &&
            showErrors &&
            this.getErrorMessages(errors)}

          {error &&
            <div class="alert alert-danger alert-container">
              {error}
            </div>}

          {this.state.invitationLetterId && (
            <div className={"alert alert-success alert-container"}>
              Invitation Letter request has been received. Invitation Letter
              Request ID : {this.state.invitationLetterId}, for future
              enquiries.
            </div>
          )}
        </form>
      </div>
    );
  }
}

export default InvitationLetterForm;
