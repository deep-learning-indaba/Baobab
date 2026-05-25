import React, { Component } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import { withTranslation } from 'react-i18next'

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

    userService.requestPasswordReset(this.state.email)
      .then(response => {
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
    const { loading,
      error,
      resetRequested
    } = this.state;

    const t = this.props.t;

    if (resetRequested) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[75vh] py-12 px-4 sm:px-6 lg:px-8 text-center">
          <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-border p-8 space-y-4">
            <h1 className="font-heading text-xl font-bold tracking-tight text-foreground">{t("Reset Password")}</h1>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {t("Your password reset request has been processed. Please check your email for a link that will allow you to change your password.")}
            </p>
          </div>
        </div>
      )
    }

    return (
      <div className="flex flex-col items-center justify-center min-h-[75vh] py-12 px-4 sm:px-6 lg:px-8 text-left">
        <form onSubmit={this.handleSubmit} className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6">
          <div className="text-center space-y-2">
            <h3 className="font-heading text-xl font-bold tracking-tight text-foreground">{t("Reset Password")}</h3>
            <p className="text-sm text-muted-foreground">
              {t("Enter your email address below, and we will email you a password reset link.")}
            </p>
          </div>

          <div className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="email" className="block text-sm font-semibold text-foreground/90">{t("Email Address")}</label>
              <input
                type="email"
                className="w-full border border-border rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all bg-white"
                id="email"
                onChange={this.handleChange}
                value={this.state.email}
                autoFocus={true} />
            </div>

            <div className="pt-2">
              <button
                type="submit"
                className="w-full inline-flex items-center justify-center px-5 py-3 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50 cursor-pointer"
                disabled={!this.validateForm() || loading}>
                {loading && (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-1.5"></div>
                )}
                {t("Reset Password")}
              </button>
            </div>

            {error && (
              <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-4">
                {error}
              </div>
            )}
          </div>
        </form>
      </div>
    );
  }
}

export default withRouter(withTranslation()(RequestPasswordResetForm));
