import React, { Component } from "react";
import { userService } from "../../../services/user";
import { Link } from "react-router-dom";
import { withRouter } from "react-router";
import { Trans, withTranslation } from 'react-i18next'

class VerifyEmailComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      loading: false,
      error: ""
    };
  }

  componentDidMount() {
    if (this.props.location && this.props.location.search) {
      this.setState({
        verifyToken: this.props.location.search.substring(this.props.location.search.indexOf('=') + 1),
        loading: true
      }, () => {
        userService.verifyEmail(this.state.verifyToken).then(response => {
          this.setState({
            error: response.error,
            loading: false
          }, () => {
            // Redirect to login after short delay to allow user to see that their email was verified.
            setTimeout(() => {
              this.props.history.push("/login");
            }, 3000);
          });
        })
      });
    } else {
      this.setState({
        error: "No verification token provided."
      });
    }
  }

  render() {
    const { error, loading } = this.state;

    const loadingStyle = {
      "width": "3rem",
      "height": "3rem"
    }

    if (loading) {
      return (
        <div class="d-flex justify-content-center">
          <div class="spinner-border" style={loadingStyle} role="status">
            <span class="sr-only">Loading...</span>
          </div>
        </div>
      )
    }

    if (error) {
      return <div class="alert alert-danger alert-container">
        {error}
      </div>
    }

    const t = this.props.t;

    return (
      <div className={"verify-email"}>
        <p className="h5 text-center mb-4">{t("Verify Email Address")}</p>
        <div class="col">
          <Trans i18nKey="verified">Your email address has been verified. <Link to="/login">Click here</Link> to login if you are not automatically redirected.</Trans>
          </div>
      </div>
    )
  }
}

export default withRouter(withTranslation()(VerifyEmailComponent));