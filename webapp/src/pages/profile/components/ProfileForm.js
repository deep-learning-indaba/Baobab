import React, { Component } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import { ConfirmModal } from "../../../components/Modal";
import validationFields from "../../../utils/validation/validationFields";
import { getTitleOptions } from "../../../utils/validation/contentHelpers";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import { requiredText, requiredDropdown } from "../../../utils/validation/rules.js";
import { withTranslation } from 'react-i18next';

const fieldValidations = [
  ruleRunner(validationFields.title, requiredDropdown),
  ruleRunner(validationFields.firstName, requiredText),
  ruleRunner(validationFields.lastName, requiredText),
];

class ProfileForm extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: {},
      showErrors: false,
      submitted: false,
      loading: false,
      errors: [],
      confirmResetVisible: false
    };
  }

  componentWillMount() {
    Promise.all([
      getTitleOptions,
    ]).then(result => {
      this.setState({
        titleOptions: this.checkOptionsList(result[0]),
      });
    });

    userService.get().then(result => {
      var date = result.user_dateOfBirth;
      if (date) date = date.split("T")[0];
      this.setState({
        user: {
          title: result.user_title,
          firstName: result.firstname,
          lastName: result.lastname,
          email: result.email
        }
      });
    });
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

  handleChangeDropdown = (name, dropdown) => {
    this.setState({
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

  deleteAccount = () => {
    userService.deleteAccount()
      .then(
        response => {
          const { from } = this.props.location.state || {
            from: { pathname: "/" }
          };
          this.props.history.push(from);
        },
        error => this.setState({ error, loading: false })
      );
    if (this.props.logout) {
      this.props.logout();
    }
  };

  resetPassword = () => {
    userService.requestPasswordReset(this.state.user.email)
      .then(response => {
        if (response.status === 201) {
          const { from } = { from: { pathname: "/" } };
          this.props.history.push(from);
        } else {
          this.setState({
            error: response.messsage,
            loading: false,
            confirmResetVisible: false
          });
        }
      });
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

  handleSubmit = event => {
    event.preventDefault();
    this.setState({ submitted: true, showErrors: true });

    if (
      this.state.errors &&
      this.state.errors.$set &&
      this.state.errors.$set.length > 0
    )
      return;
    this.setState({ loading: true });

    userService.update(this.state.user).then(
      user => {
        if (this.props.loggedIn) {
          this.props.loggedIn(user);
        }
        const { from } = this.props.location.state || {
          from: { pathname: "/" }
        };
        this.props.history.push(from);
      },
      error => this.setState({ error, loading: false })
    );
  };

  getErrorMessages = errors => {
    let errorMessages = [];
    if (errors.$set === null) return;

    let arr = errors.$set;
    for (let i = 0; i < arr.length; i++) {
      errorMessages.push(
        <div key={i} className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-4">
          {Object.values(arr[i])}
        </div>
      );
    }
    return errorMessages;
  };

  render() {
    const {
      firstName,
      lastName,
      title,
      email
    } = this.state.user;

    const t = this.props.t;

    const titleValue = this.getContentValue(this.state.titleOptions, title);

    const { loading,
      errors,
      showErrors
    } = this.state;

    return (
      <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-6">
        <form onSubmit={this.handleSubmit} className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6">
          <div className="border-b border-border/50 pb-4">
            <h1 className="font-heading text-2xl font-bold text-foreground">{t("Your Profile")}</h1>
          </div>

          <div className="space-y-4">
            <FormSelect
              options={this.state.titleOptions}
              id={validationFields.title.name}
              onChange={this.handleChangeDropdown}
              value={titleValue}
              label={t(validationFields.title.display)} />
            <FormTextBox
              id={validationFields.firstName.name}
              type="text"
              onChange={this.handleChange(validationFields.firstName)}
              value={firstName}
              label={t(validationFields.firstName.display)} />
            <FormTextBox
              id={validationFields.lastName.name}
              type="text"
              onChange={this.handleChange(validationFields.lastName)}
              value={lastName}
              label={t(validationFields.lastName.display)}
              editable={false} />
            <FormTextBox
              isDisabled={true}
              id={validationFields.email.name}
              type="email"
              value={email}
              label={t(validationFields.email.display)}
              description={t("Read-only")} />

            <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-6 border-t border-border/50">
              <button
                type="button"
                className="text-primary hover:underline font-semibold cursor-pointer text-sm"
                disabled={loading}
                onClick={() => this.setState({ confirmResetVisible: true })}>
                {t("Reset Your Password")}
              </button>

              <button
                type="submit"
                className="inline-flex items-center justify-center px-5 py-3 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50 cursor-pointer"
                disabled={loading}>
                {loading && (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-1.5"></div>
                )}
                {t("Save profile")}
              </button>
            </div>
          </div>

          {errors && errors.$set && showErrors && this.getErrorMessages(errors)}
        </form>

        <ConfirmModal
          visible={this.state.confirmResetVisible}
          onOK={this.resetPassword}
          onCancel={() => this.setState({ confirmResetVisible: false })}
          okText={t("Reset Password")}
          cancelText={"Cancel"}>
          <p>
            {t("Are you sure? Click 'Reset Password' to receive an email with a link to reset your password.")}
          </p>
        </ConfirmModal>
      </div>
    );
  }
}

export default withRouter(withTranslation()(ProfileForm));
