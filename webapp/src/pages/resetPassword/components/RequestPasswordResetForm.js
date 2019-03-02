import React, { Component } from "react";
import { userService } from "../../../services/user";
import { Link } from "react-router-dom";
import { withRouter } from "react-router";
import { createColClassName } from "../../../utils/styling/styling";

class RequestPasswordResetForm extends Component {
  constructor(props) {
    super(props);

    this.state = {
      email: "",
      submitted: false,
      loading: false,
      error: ""
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
    this.setState({ submitted: true });
    this.setState({ loading: true });

    userService.requestPasswordReset(this.state.email).then(response => {
      console.log("Response from user service: ", response);
      if (response.status === 201) {
        const { from } = { from: { pathname: "/" } };
        this.props.history.push(from);
      } else {
        this.setState({
          error: response.messsage,
          loading: false
        });
      }
    });
  };

  render() {
    const xs = 6;
    const sm = 6;
    const md = 6;
    const lg = 6;
    const commonColClassName = createColClassName(xs, sm, md, lg);
    const { email, submitted, loading, error } = this.state;

    return (
      <div className="Login">
        {error && <div className={"alert alert-danger"}>{error}</div>}
        <form onSubmit={this.handleSubmit}>
          <p className="h5 text-center mb-4">Sign in</p>
          <div class="form-group">
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
          <div class="row">
            <div class={commonColClassName}>
              <button
                type="submit"
                class="btn btn-primary"
                disabled={!this.validateForm() || loading}
              >
                Reset password
              </button>
            </div>
          </div>
          {
            loading && (
              <img src="data:image/gif;base64,R0lGODlhEAAQAPIAAP///wAAAMLCwkJCQgAAAGJiYoKCgpKSkiH/C05FVFNDQVBFMi4wAwEAAAAh/hpDcmVhdGVkIHdpdGggYWpheGxvYWQuaW5mbwAh+QQJCgAAACwAAAAAEAAQAAADMwi63P4wyklrE2MIOggZnAdOmGYJRbExwroUmcG2LmDEwnHQLVsYOd2mBzkYDAdKa+dIAAAh+QQJCgAAACwAAAAAEAAQAAADNAi63P5OjCEgG4QMu7DmikRxQlFUYDEZIGBMRVsaqHwctXXf7WEYB4Ag1xjihkMZsiUkKhIAIfkECQoAAAAsAAAAABAAEAAAAzYIujIjK8pByJDMlFYvBoVjHA70GU7xSUJhmKtwHPAKzLO9HMaoKwJZ7Rf8AYPDDzKpZBqfvwQAIfkECQoAAAAsAAAAABAAEAAAAzMIumIlK8oyhpHsnFZfhYumCYUhDAQxRIdhHBGqRoKw0R8DYlJd8z0fMDgsGo/IpHI5TAAAIfkECQoAAAAsAAAAABAAEAAAAzIIunInK0rnZBTwGPNMgQwmdsNgXGJUlIWEuR5oWUIpz8pAEAMe6TwfwyYsGo/IpFKSAAAh+QQJCgAAACwAAAAAEAAQAAADMwi6IMKQORfjdOe82p4wGccc4CEuQradylesojEMBgsUc2G7sDX3lQGBMLAJibufbSlKAAAh+QQJCgAAACwAAAAAEAAQAAADMgi63P7wCRHZnFVdmgHu2nFwlWCI3WGc3TSWhUFGxTAUkGCbtgENBMJAEJsxgMLWzpEAACH5BAkKAAAALAAAAAAQABAAAAMyCLrc/jDKSatlQtScKdceCAjDII7HcQ4EMTCpyrCuUBjCYRgHVtqlAiB1YhiCnlsRkAAAOwAAAAAAAAAAAA==" />
            )
          }
          <div />
        </form>
      </div>
    );
  }
}

export default withRouter(RequestPasswordResetForm);
