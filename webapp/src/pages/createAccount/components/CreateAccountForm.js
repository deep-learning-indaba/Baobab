import React, { Component } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import validationFields from "../../../utils/validation/validationFields";
import { getTitleOptions } from "../../../utils/validation/contentHelpers";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import {
  requiredText,
  requiredDropdown,
  validEmail
} from "../../../utils/validation/rules.js";
import { createColClassName } from "../../../utils/styling/styling";

const fieldValidations = [
  ruleRunner(validationFields.title, requiredDropdown),
  ruleRunner(validationFields.firstName, requiredText),
  ruleRunner(validationFields.lastName, requiredText),
  ruleRunner(validationFields.email, validEmail),
  ruleRunner(validationFields.password, requiredText),
  ruleRunner(validationFields.confirmPassword, requiredText),
];

class CreateAccountForm extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: {
        email: "",
        password: "",
        confirmPassword: ""
      },
      showErrors: false,
      submitted: false,
      loading: false,
      errors: [],
      titleOptions: [],
      error: "",
      created: false,
      over18: false,
      agreePrivacyPolicy: false
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
    Promise.all([
      getTitleOptions,
    ]).then(result => {
      this.setState({
        titleOptions: this.checkOptionsList(result[0]),
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

  toggleAge = () => {
    let currentOver18 = this.state.over18;
    this.setState({ over18: !currentOver18 });
  };

  togglePrivacyPolicy = () => {
    let currentPrivacyPolicy = this.state.agreePrivacyPolicy;
    this.setState({ agreePrivacyPolicy: !currentPrivacyPolicy });
  };


  handleSubmit = event => {
    event.preventDefault();
    this.setState({ submitted: true, showErrors: true });

    if (this.state.user.password !== this.state.user.confirmPassword) {
      this.state.errors.$set.push({ passwords: "Passwords do not match" });
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
    const xs = 12;
    const sm = 4;
    const md = 4;
    const lg = 4;
    const commonColClassName = createColClassName(xs, sm, md, lg);

    const {
      firstName,
      lastName,
      email,
      title,
      password,
      confirmPassword
    } = this.state.user;

    const {
      loading,
      errors,
      showErrors,
      error,
      created,
      over18,
      agreePrivacyPolicy
    } = this.state;

    if (created) {
      return (
        <div className="CreateAccount">
          <p className="h5 text-center mb-4">Create Account</p>
          <p className="account-created">
            Your {this.props.organisation ? this.props.organisation.name : ""} account
            has been created, but before you can use it, we
            need to verify your email address. Please check your email (and spam
            folder) for a message containing a link to verify your email
            address.
          </p>
        </div>
      );
    }

    const titleValue = this.getContentValue(this.state.titleOptions, title);

    return (
      <div className="CreateAccount">
        <form onSubmit={this.handleSubmit}>
          <p className="h5 text-center mb-4">Create Account</p>
          <div class="row">
            <div class={commonColClassName}>
              <FormSelect
                options={this.state.titleOptions}
                id={validationFields.title.name}
                placeholder={validationFields.title.display}
                onChange={this.handleChangeDropdown}
                value={titleValue}
                label={validationFields.title.display}
              />
            </div>

            <div class={commonColClassName}>
              <FormTextBox
                id={validationFields.firstName.name}
                type="text"
                placeholder={validationFields.firstName.display}
                onChange={this.handleChange(validationFields.firstName)}
                value={firstName}
                label={validationFields.firstName.display}
              />
            </div>

            <div class={commonColClassName}>
              <FormTextBox
                id={validationFields.lastName.name}
                type="text"
                placeholder={validationFields.lastName.display}
                onChange={this.handleChange(validationFields.lastName)}
                value={lastName}
                label={validationFields.lastName.display}
              />
            </div>
          </div>

          <div class="row">
            <div class={commonColClassName}>
              <FormTextBox
                id={validationFields.email.name}
                type="email"
                placeholder={validationFields.email.display}
                onChange={this.handleChange(validationFields.email)}
                value={email}
                label={validationFields.email.display}
              />
            </div>

            <div class={commonColClassName}>
              <FormTextBox
                id={validationFields.password.name}
                type="password"
                placeholder={validationFields.password.display}
                onChange={this.handleChange(validationFields.password)}
                value={password}
                label={validationFields.password.display}
              />
            </div>

            <div class={commonColClassName}>
              <FormTextBox
                id={validationFields.confirmPassword.name}
                type="password"
                placeholder={validationFields.confirmPassword.display}
                onChange={this.handleChange(validationFields.confirmPassword)}
                value={confirmPassword}
                label={validationFields.confirmPassword.display}
              />
            </div>
          </div>

          <div>
            <br />
            <h5>Please confirm the following in order to create an account</h5>

            <div className="form-check">
              <input
                className="form-check-input"
                id="over18"
                name="over18"
                type="checkbox"
                checked={over18}
                onChange={this.toggleAge} />
              <label class="form-check-label" for="over18">
                I am over 18
              </label>
            </div>

            <div className="form-check">
              <input
                className="form-check-input"
                name="agreePrivacyPolicy"
                id="agreePrivacyPolicy"
                type="checkbox"
                checked={agreePrivacyPolicy}
                onChange={this.togglePrivacyPolicy}
              />
              <label class="form-check-label" for="agreePrivacyPolicy">
                {"I have read and agree to the "}
                <a href={"/" + (this.props.organisation ? this.props.organisation.privacy_policy : "")}
                  target="_blank">
                  privacy policy
                </a>
              </label>
            </div>
          </div>

          <br></br><br></br>

          <button
            type="submit"
            class="btn btn-primary"
            disabled={!this.validateForm() || loading || !agreePrivacyPolicy || !over18}>
            {loading && (
              <span
                class="spinner-grow spinner-grow-sm"
                role="status"
                aria-hidden="true"
              />
            )}
            Sign Up
          </button>
          {errors &&
            errors.$set &&
            showErrors &&
            this.getErrorMessages(errors)}
          {error &&
            <div class="alert alert-danger alert-container">
              {error}
            </div>}
        </form>
      </div>
    );
  }
}

export default withRouter(CreateAccountForm);
