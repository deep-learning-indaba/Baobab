import React, { Component } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import { ConfirmModal } from "react-bootstrap4-modal";
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
        <div className={"alert alert-danger alert-container"}>
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
      <div className="Profile">
        <form onSubmit={this.handleSubmit}>

          <div class="Profile-Header">
            <h3>{t("Your Profile")}</h3>
          </div>

          <div class="card">

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

            <br /><br />

            <button
              type="submit"
              class="btn btn-primary Button"
              disabled={loading}>
              {loading && (
                <span
                  class="spinner-grow spinner-grow-sm"
                  role="status"
                  aria-hidden="true" />
              )}
                {t("Save profile")}
              </button>
          </div>
          <br/>
          <button
            type="button"
            class="link-style App-link"
            disabled={loading}
            onClick={() => this.setState({ confirmResetVisible: true })}>
            {t("Reset Your Password")}
          </button>

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
