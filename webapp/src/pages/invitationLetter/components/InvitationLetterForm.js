import React, { Component } from "react";
import { createColClassName } from "../../../utils/styling/styling";
import validationFields from "../../../utils/validation/validationFields";
import FormTextBox from "../../../components/form/FormTextBox";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import { requiredText } from "../../../utils/validation/rules.js";

const fieldValidations = [
  ruleRunner(validationFields.passportNumber, requiredText),
  ruleRunner(validationFields.fullNameOnPassport, requiredText),
  ruleRunner(validationFields.passportIssuedByAuthority, requiredText)
];
class InvitationLetterForm extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: {
        countryOfResidence: null,
        nationality: null,
        dateOfBirth: null,
        passportNumber: "",
        fullNameOnPassport: "",
        passportIssuedByAuthority: ""
      },
      submitted: false,
      loading: false,
      errors: []
    };
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
      this.state.user.passportIssuedByAuthority.length > 0
    );
  }
  handleSubmit = event => {
    event.preventDefault();
    this.setState({ submitted: true, showErrors: true });
  };
  render() {
    const {
      passportNumber,
      fullNameOnPassport,
      passportIssuedByDate,
      passportIssuedByAuthority
    } = this.state.user;

    const { loading, errors, showErrors, error, created } = this.state;

    const passportDetailsStyle = createColClassName(12, 2, 3, 3);
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
