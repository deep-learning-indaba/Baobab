import React, { Component } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import { createColClassName } from "../../../utils/styling/styling";

class RequestPasswordResetForm extends Component {
  constructor(props) {
    super(props);

    this.state = {
      email: "",
      submitted: false,
      loading: false,
      error: "",
      resetRequested: false
    };
  }
  validateForm() {
    return this.state.email.length > 0;
  }

  handleChange = event => {
    this.setState({
      [event.target.id]: event.target.value
    });
  };

  handleSubmit = event => {
    event.preventDefault();
    this.setState({
      submitted: true,
      loading: true
    });

    userService.requestPasswordReset(this.state.email).then(response => {
      if (response.status === 201) {
        this.setState({
          resetRequested: true
        });
      } else {
        this.setState({
          error: response.message,
          loading: false
        });
      }
    });
  };

  render() {
    const xs = 8;
    const sm = 8;
    const md = 8;
    const lg = 8;
    const commonColClassName = createColClassName(xs, sm, md, lg);
    const { loading, error, resetRequested } = this.state;

    if (resetRequested) {
      return (
        <div className={"reset-status text-center"}>
          <p className="h5 text-center mb-4">Reset Password</p>
          <div class="col">
            Your password reset request has been processed. Please check your email for a link that will allow you to change your password.
          </div>
        </div>
      )
    }

    console.log("Rendering, error is: " + error);

    return (
      <div className="Login">
        <form onSubmit={this.handleSubmit}>
          <p className="h5 text-center mb-4">Reset Password</p>
          <div class="form-group reset-password-container">
            <label for="email">Email address</label>
            <input
              type="email"
              class="form-control"
              id="email"
              placeholder="Enter email"
              onChange={this.handleChange}
              value={this.state.email}
              autoFocus="true"
            />
          </div>
          <div class="row, center">
            <div class={commonColClassName}>
              <button
                type="submit"
                class="btn btn-primary"
                disabled={!this.validateForm() || loading}
              >
                {loading && <span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span>}
                Reset password
              </button>
            </div>
            {error && 
              <div className={"alert alert-danger alert-container"}>
                {error}
              </div>}
          </div>
          <div />
        </form>
      </div>
    );
  }
}

export default withRouter(RequestPasswordResetForm);
