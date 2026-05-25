import React, { Component } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import FormTextBox from "../../../components/form/FormTextBox";
import validationFields from "../../../utils/validation/validationFields";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import { requiredText } from "../../../utils/validation/rules.js";
import { withTranslation } from 'react-i18next'

const fieldValidations = [
  ruleRunner(validationFields.password, requiredText),
  ruleRunner(validationFields.confirmPassword, requiredText)
];

class ConfirmPasswordResetForm extends Component {
  constructor(props) {
    super(props);

    this.state = {
      password: "",
      confirmPassword: "",
      token: this.props.token,
      submitted: false,
      loading: false,
      error: ""
    };
  }

  validateForm() {
    return (
      this.state.password.length > 0 &&
      this.state.confirmPassword.length > 0 &&
      this.state.password === this.state.confirmPassword
    );
  }

  handleChange = field => {
    return event => {
      this.setState({
        [field.name]: event.target.value
      },
        function () {
          let errorsForm = run(this.state, fieldValidations);
          this.setState({ errors: { $set: errorsForm } });
        }
      );
    };
  };


  handleSubmit = event => {
  event.preventDefault();

    this.setState({
      submitted: true,
      loading: true
    });

   const _this = this;

    return new Promise(function (resolve) {
      userService
        .confirmPasswordReset(_this.state.password, _this.state.token)
        .then(response => {
          console.log("Response from user service: ", response);

          if (response.status === 201) {
            const { from } = { from: { pathname: "/login" } };
            _this.props.history.push(from);
          } else {

            _this.setState({
              error: response.message,
              loading: false
            });
          }
          resolve(response.message)
        });
    })

  };

  render() {
    const {
      password,
      confirmPassword,
      loading,
      error
    } = this.state;

    const t = this.props.t;

    return (
      <div className="flex flex-col items-center justify-center min-h-[75vh] py-12 px-4 sm:px-6 lg:px-8 text-left">
        <form onSubmit={this.handleSubmit} className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6">
          <div className="text-center space-y-2">
            <h3 className="font-heading text-xl font-bold tracking-tight text-foreground">{t("Reset Password")}</h3>
            <p className="text-sm text-muted-foreground">
              {t("Please enter and confirm your new password below.")}
            </p>
          </div>

          <div className="space-y-4">
            <FormTextBox
              id={validationFields.password.name}
              type="password"
              placeholder={t(validationFields.password.display)}
              onChange={this.handleChange(validationFields.password)}
              value={password}
              label={t(validationFields.password.display)}
            />

            <FormTextBox
              id={validationFields.confirmPassword.name}
              type="password"
              placeholder={t(validationFields.confirmPassword.display)}
              onChange={this.handleChange(validationFields.confirmPassword)}
              value={confirmPassword}
              label={t(validationFields.confirmPassword.display)}
            />

            <div className="pt-2">
              <button
                type="submit"
                className="w-full inline-flex items-center justify-center px-5 py-3 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50 cursor-pointer"
                disabled={!this.validateForm() || loading}>
                {loading && (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-1.5"></div>
                )}
                {t("Submit")}
              </button>
            </div>

            {error && (
              <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-4">
                {error}
              </div>
            )}
          </div>
        </form>
      </div>
    );
  }
}

export default withRouter(withTranslation()(ConfirmPasswordResetForm));
