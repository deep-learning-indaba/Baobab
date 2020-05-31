import React, { Component } from "react";
import { userService } from "../../../services/user";
import { Link } from "react-router-dom";
import { withRouter } from "react-router";
import { createColClassName } from "../../../utils/styling/styling";

class LoginForm extends Component {
  constructor(props) {
    super(props);

    this.state = {
      email: "",
      password: "",
      loading: false,
      notVerified: false,
      error: "",
      resendStatus: ""
    };
  }

  validateForm() {
    return this.state.email.length > 0 && this.state.password.length > 0;
  }

  handleChange = event => {
    this.setState({
      [event.target.id]: event.target.value
    });
  };

  handleSubmit = event => {
    event.preventDefault();
    this.setState({ loading: true });

    userService.login(this.state.email, this.state.password).then(
      user => {

        if (this.props.loggedIn) {
          this.props.loggedIn(user);
        }
        // Login was successful, redirect to referring location.
        if (this.props.location.state) {
          this.props.history.push(this.props.location.state);
        }
        else {
          //  TODO Fix properly
          // this.props.history.goBack();
          this.props.history.push('/')
        }

      },
      e =>
        this.setState({
          error:
            e.response && e.response.data ?
              e.response.data.message : e.message,
          loading: false,
          notVerified: e.response && e.response.status === 422
        })
    );
  };

  resendVerification = event => {
    event.preventDefault();
    this.setState({ loading: true });
    userService.resendVerification(this.state.email).then(resp => {
      this.setState({
        loading: false,
        error: resp.error,
        resendStatus: resp.error ? "" : "We have re-sent your verification email, please check your inbox (and spam) and click on the link to verify your email address.",
        email: "",
        password: ""
      });
    });
  }

  render() {
    const xs = 6;
    const sm = 6;
    const md = 6;
    const lg = 6;
    const commonColClassName = createColClassName(xs, sm, md, lg);

    const { email,
      password,
      loading,
      error,
      notVerified,
      resendStatus
    } = this.state;

    return (
      <div className="Login">

        <form
          style={{ margin: "10px" }}
          onSubmit={this.handleSubmit}>

          <div class="login-header-logo">
            <img src={this.props.organisation && require("../../../images/" + this.props.organisation.small_logo)} />
            <h3>Sign in to your account</h3>
            <h6>Or <Link to="/createAccount" className="sign-up">Sign Up</Link> for a new one</h6>
          </div>

          <div class="card">
            <div class="form-group">
              <label for="email">Email address</label>
              <input
                type="email"
                class="form-control"
                id="email"
                onChange={this.handleChange}
                value={email}
                autoFocus="true" />
            </div>

            <div class="form-group">
              <label for="password">Password</label>
              <input
                type="password"
                class="form-control"
                id="password"
                onChange={this.handleChange}
                value={password} />
              <div class="forgot-password">
                <Link to="/resetPassword">Forgot your password?</Link>
              </div>
            </div>

            <div class="row">

              <button
                id="btn-login"
                type="submit"
                class="btn btn-primary"
                disabled={!this.validateForm() || loading}>
                {loading && (
                  <span
                    class="spinner-grow spinner-grow-sm"
                    role="status"
                    aria-hidden="true" />
                )}
                  Sign In
                </button>

            </div>



            {error &&
              <div id="error-login" className={"alert alert-danger alert-container"}>
                {error}
                {notVerified &&
                  <button className="link-style"
                    onClick={this.resendVerification}>
                    Resend Verification Email
                </button>}
              </div>}

            {resendStatus &&
              <div className={"alert alert-success alert-container"}>
                {resendStatus}
              </div>}


          </div>
        </form>
      </div>
    );
  }
}

export default withRouter(LoginForm);
