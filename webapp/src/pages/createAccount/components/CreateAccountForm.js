import React, { Component, Suspense } from "react";
import { getImage } from "../../../utils/images";
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
  validatePassword,
  matchingPasswords
} from "../../../utils/validation/rules.js";

const PassStrengthBar = React.lazy(() => import("./PassStrength"));

const fieldValidations = [
  ruleRunner(validationFields.title, requiredDropdown),
  ruleRunner(validationFields.firstName, requiredText),
  ruleRunner(validationFields.lastName, requiredText),
  ruleRunner(validationFields.email, validEmail),
  ruleRunner(validationFields.password, requiredText),
  ruleRunner(validationFields.confirmPassword, requiredText),
  ruleRunner(validationFields.confirmPassword, matchingPasswords),
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
      <div className="flex flex-col items-center justify-center min-h-[75vh] py-12 px-4 sm:px-6 lg:px-8 text-left">
        <form onSubmit={this.handleSubmit} className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6">
          <div className="text-center space-y-2">
            {this.props.organisation && (
              <img
                src={getImage(this.props.organisation.small_logo)}
                alt="Logo"
                className="mx-auto h-16 w-16 object-contain mb-4 rounded-xl border border-border/50 p-1"
              />
            )}
            <h3 className="font-heading text-xl font-bold tracking-tight text-foreground">{t("Sign Up")}</h3>
            <h6 className="text-sm text-muted-foreground">
              <Link to="/login" className="text-primary hover:underline font-semibold">
                {t("Sign In")}
              </Link>{" "}
              {t("if you already have an account")}
            </h6>
          </div>

          <div className="space-y-4">
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
            <FormTextBox
              id={validationFields.password.name}
              type="password"
              onChange={this.handleChange(validationFields.password)}
              value={password}
              label={t(validationFields.password.display)}
            />
            <Suspense fallback={<div className="text-xs text-muted-foreground">Loading...</div>}>
              <PassStrengthBar password={this.state.user.password} />
            </Suspense>

            <FormTextBox
              id={validationFields.confirmPassword.name}
              type="password"
              onChange={this.handleChange(validationFields.confirmPassword)}
              value={confirmPassword}
              label={t(validationFields.confirmPassword.display)}
            />

            <div className="space-y-3 pt-2">
              <div className="flex items-start gap-2.5">
                <input
                  id="over18"
                  name="over18"
                  type="checkbox"
                  checked={over18}
                  onChange={this.toggleAge}
                  className="rounded border-border text-primary focus:ring-primary w-4 h-4 cursor-pointer mt-0.5"
                />
                <label htmlFor="over18" className="text-sm text-muted-foreground cursor-pointer select-none">
                  {t("I am over 18")}
                </label>
              </div>

              <div className="flex items-start gap-2.5">
                <input
                  name="agreePrivacyPolicy"
                  id="agreePrivacyPolicy"
                  type="checkbox"
                  checked={agreePrivacyPolicy}
                  onChange={this.togglePrivacyPolicy}
                  className="rounded border-border text-primary focus:ring-primary w-4 h-4 cursor-pointer mt-0.5"
                />
                <label htmlFor="agreePrivacyPolicy" className="text-sm text-muted-foreground cursor-pointer select-none">
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
                    className="text-primary hover:underline font-semibold"
                  >
                    {t("Privacy Policy")}
                  </a>
                </label>
              </div>
            </div>

            <div className="pt-2">
              <button
                id="btn-signup-confirm"
                type="submit"
                className="w-full inline-flex items-center justify-center px-5 py-3 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50 cursor-pointer"
                disabled={
                  !this.validateForm() ||
                  loading ||
                  !agreePrivacyPolicy ||
                  !over18
                }
              >
                {loading && (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-1.5"></div>
                )}
                {t("Sign Up")}
              </button>
            </div>
          </div>

          {errors && errors.$set && showErrors && this.getErrorMessages(errors)}
          {error && (
            <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-4">{error}</div>
          )}
        </form>
      </div>
    );
  }
}

export default withRouter(withTranslation()(CreateAccountForm));
