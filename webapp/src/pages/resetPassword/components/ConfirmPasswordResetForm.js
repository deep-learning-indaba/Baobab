import React, { Component } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import FormTextBox from "../../../components/form/FormTextBox";
import validationFields from "../../../utils/validation/validationFields";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import { requiredText } from "../../../utils/validation/rules.js";

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

    return (
      <div className="ResetPassword">
        {error &&
          <div className={"alert alert-danger alert-container"}>
            {error}
          </div>}

        <form onSubmit={this.handleSubmit}>
          <p className="h5 text-center mb-4">Reset password</p>

          <div className="col">
            <div>
              <FormTextBox
                id={validationFields.password.name}
                type="password"
                placeholder={validationFields.password.display}
                onChange={this.handleChange(validationFields.password)}
                value={password}
                label={validationFields.password.display} />
            </div>

            <div>
              <FormTextBox
                id={validationFields.confirmPassword.name}
                type="password"
                placeholder={validationFields.confirmPassword.display}
                onChange={this.handleChange(validationFields.confirmPassword)}
                value={confirmPassword}
                label={validationFields.confirmPassword.display} />
            </div>

            <div>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={!this.validateForm() || loading}>
                {loading && <span className="spinner-grow spinner-grow-sm"
                  role="status"
                  aria-hidden="true"></span>}
                Submit
              </button>
            </div>
          </div>
        </form>
      </div>
    );
  }
}

export default withRouter(ConfirmPasswordResetForm);
