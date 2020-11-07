import React, { Component, lazy, useEffect, useState } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import validationFields from "../../../utils/validation/validationFields";
import { getTitleOptions } from "../../../utils/validation/contentHelpers";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import { Link } from "react-router-dom";
import { withTranslation } from "react-i18next";
import {
  requiredText,
  requiredDropdown,
  validEmail,
  validatePassword
} from "../../../utils/validation/rules.js";
import PasswordStrengthBar from "react-password-strength-bar";

const fieldValidations = [
  ruleRunner(validationFields.title, requiredDropdown),
  ruleRunner(validationFields.firstName, requiredText),
  ruleRunner(validationFields.lastName, requiredText),
  ruleRunner(validationFields.email, validEmail),
  ruleRunner(validationFields.password, requiredText),
  ruleRunner(validationFields.confirmPassword, requiredText)
];

class CreateAccountForm extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: {
        email: "",
        password: "",
        confirmPassword: "",
        agreePrivacyPolicy: false
      },
      showErrors: false,
      submitted: false,
      loading: false,
      errors: [],
      titleOptions: [],
      error: "",
      created: false,
      over18: false
    };
  }

  getContentValue(options, value) {
    if (options && options.filter) {
      return options.filter(option => {
        return option.value === value;
      });
    } else return null;
  }

  checkOptionsList(optionsList) {
    if (Array.isArray(optionsList)) {
      return optionsList;
    } else return [];
  }

  componentWillMount() {
    Promise.all([getTitleOptions]).then(result => {
      this.setState({
        titleOptions: this.checkOptionsList(result[0])
      });
    });
  }

  validateForm() {
    return (
      this.state.user.email.length > 0 &&
      this.state.user.password.length > 0 &&
      this.state.user.confirmPassword.length > 0
    );
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

  toggleAge = () => {
    let currentOver18 = this.state.over18;
    this.setState({ over18: !currentOver18 });
  };

  togglePrivacyPolicy = () => {
    let currentPrivacyPolicy = this.state.user.agreePrivacyPolicy;
    this.setState({
      user: { ...this.state.user, agreePrivacyPolicy: !currentPrivacyPolicy }
    });
  };

  handleSubmit = event => {
    event.preventDefault();
    this.setState({ submitted: true, showErrors: true });

    if (this.state.user.password !== this.state.user.confirmPassword) {
      this.state.errors.$set.push({
        passwords: this.props.t("Passwords do not match")
      });
    }
    const passwordErrors = validatePassword(this.state.user.password);
    if (
      passwordErrors &&
      passwordErrors.password &&
      passwordErrors.password.length > 0 &&
      passwordErrors.password.foreach
    ) {
      passwordErrors.password.foreach(i => {
        this.state.errors.$set.push({ passwords: i });
      });
    }

    if (
      this.state.errors &&
      this.state.errors.$set &&
      this.state.errors.$set.length > 0
    )
      return;

    this.setState({ loading: true });

    userService.create(this.state.user).then(
      user => {
        this.setState({
          loading: false,
          created: true
        });
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
    const t = this.props.t;

    const {
      firstName,
      lastName,
      email,
      title,
      password,
      confirmPassword,
      agreePrivacyPolicy
    } = this.state.user;

    const { loading, errors, showErrors, error, created, over18 } = this.state;

    if (created) {
      return (
        <div className="CreateAccount">
          <p className="h3 text-center mb-4">{t("Sign Up")}</p>
          <p id="account-created">
            {this.props.t("Your")}{" "}
            {this.props.organisation ? this.props.organisation.name : ""}{" "}
            {this.props.t(
              "account has been created, but before you can use it, we need to verify your email address. Please check your email (and spam folder) for a message containing a link to verify your email address."
            )}
          </p>
        </div>
      );
    }

    const titleValue = this.getContentValue(this.state.titleOptions, title);

    return (
      <div className="CreateAccount">
        <form onSubmit={this.handleSubmit}>
          <div class="login-header-logo text-center">
            <img
              src={
                this.props.organisation &&
                require("../../../images/" + this.props.organisation.small_logo)
              }
              alt="Logo"
            />
            <h3>{t("Sign Up")}</h3>
            <h6>
              <Link to="/login" className="sign-up">
                {t("Sign In")}
              </Link>{" "}
              {t("if you already have an account")}
            </h6>
          </div>

          <div class="card">
            <FormSelect
              options={this.state.titleOptions}
              id={validationFields.title.name}
              onChange={this.handleChangeDropdown}
              value={titleValue}
              label={t(validationFields.title.display)}
            />
            <FormTextBox
              id={validationFields.firstName.name}
              type="text"
              onChange={this.handleChange(validationFields.firstName)}
              value={firstName}
              label={t(validationFields.firstName.display)}
            />
            <FormTextBox
              id={validationFields.lastName.name}
              type="text"
              onChange={this.handleChange(validationFields.lastName)}
              value={lastName}
              label={t(validationFields.lastName.display)}
            />
            <FormTextBox
              id={validationFields.email.name}
              type="email"
              onChange={this.handleChange(validationFields.email)}
              value={email}
              label={t(validationFields.email.display)}
            />
            <div className="vertical-space"></div>
            <FormTextBox
              id={validationFields.password.name}
              type="password"
              onChange={this.handleChange(validationFields.password)}
              value={password}
              label={t(validationFields.password.display)}
            />
            <PasswordStrengthBar password={this.state.user.password} />
            <FormTextBox
              id={validationFields.confirmPassword.name}
              type="password"
              onChange={this.handleChange(validationFields.confirmPassword)}
              value={confirmPassword}
              label={t(validationFields.confirmPassword.display)}
            />
            <div className="vertical-space"></div>
            <div className="custom-control custom-checkbox text-left">
              <input
                className="custom-control-input"
                id="over18"
                name="over18"
                type="checkbox"
                checked={over18}
                onChange={this.toggleAge}
              />
              <label class="custom-control-label" for="over18">
                {t("I am over 18")}
              </label>
            </div>
            <div className="custom-control custom-checkbox text-left">
              <input
                className="custom-control-input"
                name="agreePrivacyPolicy"
                id="agreePrivacyPolicy"
                type="checkbox"
                checked={agreePrivacyPolicy}
                onChange={this.togglePrivacyPolicy}
              />
              <label class="custom-control-label" for="agreePrivacyPolicy">
                {t("I have read and agree to the ")}
                <a
                  href={
                    "/" +
                    (this.props.organisation
                      ? this.props.organisation.privacy_policy
                      : "")
                  }
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {t("Privacy Policy")}
                </a>
              </label>
            </div>
            <button
              id="btn-signup-confirm"
              type="submit"
              class="btn btn-primary"
              disabled={
                !this.validateForm() ||
                loading ||
                !agreePrivacyPolicy ||
                !over18
              }
            >
              {loading && (
                <span
                  class="spinner-grow spinner-grow-sm"
                  role="status"
                  aria-hidden="true"
                />
              )}
              {t("Sign Up")}
            </button>
          </div>

          {errors && errors.$set && showErrors && this.getErrorMessages(errors)}
          {error && (
            <div class="alert alert-danger alert-container">{error}</div>
          )}
        </form>
      </div>
    );
  }
}

export default withRouter(withTranslation()(CreateAccountForm));
