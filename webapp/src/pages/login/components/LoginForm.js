import React, { Component } from "react";
import { getImage } from "../../../utils/images";
import { userService } from "../../../services/user";
import { Link } from "react-router-dom";
import { withRouter } from "react-router";
import { withTranslation } from 'react-i18next';

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
        resendStatus: resp.error ? "" : this.props.t("We have re-sent your verification email, please check your inbox (and spam) and click on the link to verify your email address."),
        email: "",
        password: ""
      });
    });
  }

  render() {
    const { email,
      password,
      loading,
      error,
      notVerified,
      resendStatus
    } = this.state;

    const t = this.props.t;

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
            <h3 className="font-heading text-xl font-bold tracking-tight text-foreground">{t("Sign in to your account")}</h3>
            <h6 className="text-sm text-muted-foreground">
              {t("Or")}{" "}
              <Link to="/createAccount" className="text-primary hover:underline font-semibold">{t("Sign Up")}</Link>{" "}
              {t("for a new one")}
            </h6>
          </div>

          <div className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="email" className="block text-sm font-semibold text-foreground/90">{t("Email address")}</label>
              <input
                type="email"
                className="w-full border border-border rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all bg-white"
                id="email"
                onChange={this.handleChange}
                value={email}
                autoFocus={true} />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <label htmlFor="password" className="block text-sm font-semibold text-foreground/90">{t("Password")}</label>
                <div className="text-xs">
                  <Link to="/resetPassword" className="text-primary hover:underline font-semibold">{t("Forgot your password?")}</Link>
                </div>
              </div>
              <input
                type="password"
                className="w-full border border-border rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all bg-white"
                id="password"
                onChange={this.handleChange}
                value={password} />
            </div>

            <div className="pt-2">
              <button
                id="btn-login"
                type="submit"
                className="w-full inline-flex items-center justify-center px-5 py-3 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50 cursor-pointer"
                disabled={!this.validateForm() || loading}>
                {loading && (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-1.5"></div>
                )}
                {t("Sign In")}
              </button>
            </div>

            {error && (
              <div id="error-login" className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center flex flex-col items-center gap-2">
                <span>{error}</span>
                {notVerified && (
                  <button 
                    type="button"
                    className="text-primary hover:underline font-semibold cursor-pointer"
                    onClick={this.resendVerification}>
                    {t("Resend Verification Email")}
                  </button>
                )}
              </div>
            )}

            {resendStatus && (
              <div className="bg-green-50 text-green-700 border border-green-200 p-4 rounded-xl text-sm w-full text-center">
                {resendStatus}
              </div>
            )}
          </div>
        </form>
      </div>
    );
  }
}

export default withRouter(withTranslation()(LoginForm));
