import React, { Component } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import { ConfirmModal } from "react-bootstrap4-modal";
import validationFields from "../../../utils/validation/validationFields";
import {
  getTitleOptions,
} from "../../../utils/validation/contentHelpers";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import {
  requiredText,
  requiredDropdown,
} from "../../../utils/validation/rules.js";
import { createColClassName } from "../../../utils/styling/styling";

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

  deleteAccount = () => {
    userService.deleteAccount().then(
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
    userService.requestPasswordReset(this.state.user.email).then(response => {
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
        <div className={"alert alert-danger"}>{Object.values(arr[i])}</div>
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
      title,
      email
    } = this.state.user;

    const titleValue = this.getContentValue(this.state.titleOptions, title);

    const { loading, errors, showErrors } = this.state;

    return (
      <div className="Profile">
        <form onSubmit={this.handleSubmit}>
          <p className="h5 text-center mb-4">Profile</p>
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
                editable={false}
              />
            </div>
            <div class={commonColClassName}>
              <FormTextBox
                id={validationFields.email.name}
                type="email"
                value={email}
                label={validationFields.email.display}
                description={"Read-only"}
              />
            </div>
          </div>
          <div class="row">
            <div class={commonColClassName}>
              <button
                type="button"
                class="btn btn-primary Button"
                disabled={loading}
                onClick={() => this.setState({ confirmResetVisible: true })}
              >
                Reset password
              </button>
            </div>
            <div class={commonColClassName}>
              <button
                type="submit"
                class="btn btn-primary Button"
                disabled={loading}
              >
                {loading && (
                  <span
                    class="spinner-grow spinner-grow-sm"
                    role="status"
                    aria-hidden="true"
                  />
                )}
                Save profile
              </button>
            </div>
          </div>
          {errors && errors.$set && showErrors && this.getErrorMessages(errors)}
        </form>
        <ConfirmModal
          visible={this.state.confirmResetVisible}
          onOK={this.resetPassword}
          onCancel={() => this.setState({ confirmResetVisible: false })}
          okText={"Reset Password"}
          cancelText={"Cancel"}
        >
          <p>
            Are you sure? Click "Reset Password" to receive an email with a link
            to reset your password.
          </p>
        </ConfirmModal>
      </div>
    );
  }
}

export default withRouter(ProfileForm);
