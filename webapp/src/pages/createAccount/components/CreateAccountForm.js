import React, { Component } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import FormTextBox from "./FromTextBox";
import validationFields from "../../../utils/validation/validationFields";
class CreateAccountForm extends Component {
  constructor(props) {
    super(props);

    this.state = {
      email: "",
      password: "",
      confirmPassword: "",
      submitted: false,
      loading: false,
      error: ""
    };
  }

  validateForm() {
    return this.state.email.length > 0 && this.state.password.length > 0;
  }

  handleChange = field => {
    return event => {
      this.setState({
        [field.name]: event.target.value
      });
    };
  };

  handleSubmit = event => {
    event.preventDefault();
    this.setState({ submitted: true });

    if (this.state.password != this.state.confirmPassword) {
      return;
    }

    this.setState({ loading: true });

    userService.create(this.state.email, this.state.password).then(
      user => {
        const { from } = this.props.location.state || {
          from: { pathname: "/" }
        };
        this.props.history.push(from);
      },
      error => this.setState({ error, loading: false })
    );
  };

  render() {
    const { email, password, confirmPassword, loading, error } = this.state;

    return (
      <div className="Login">
        <form onSubmit={this.handleSubmit}>
          <FormTextBox
            id={validationFields.email.name}
            type="email"
            placeholder={validationFields.email.display}
            onChange={this.handleChange(validationFields.email)}
            value={email}
            label={validationFields.email.display}
          />
          <FormTextBox
            id={validationFields.password.name}
            type="password"
            placeholder={validationFields.password.display}
            onChange={this.handleChange(validationFields.password)}
            value={password}
            label={validationFields.password.display}
          />
          <FormTextBox
            id={validationFields.confirmPassword.name}
            type="password"
            placeholder={validationFields.confirmPassword.display}
            onChange={this.handleChange(validationFields.confirmPassword)}
            value={confirmPassword}
            label={validationFields.confirmPassword.display}
          />
          <button
            type="submit"
            class="btn btn-primary"
            disabled={!this.validateForm() || loading}
          >
            Login
          </button>
          {loading && (
            <img src="data:image/gif;base64,R0lGODlhEAAQAPIAAP///wAAAMLCwkJCQgAAAGJiYoKCgpKSkiH/C05FVFNDQVBFMi4wAwEAAAAh/hpDcmVhdGVkIHdpdGggYWpheGxvYWQuaW5mbwAh+QQJCgAAACwAAAAAEAAQAAADMwi63P4wyklrE2MIOggZnAdOmGYJRbExwroUmcG2LmDEwnHQLVsYOd2mBzkYDAdKa+dIAAAh+QQJCgAAACwAAAAAEAAQAAADNAi63P5OjCEgG4QMu7DmikRxQlFUYDEZIGBMRVsaqHwctXXf7WEYB4Ag1xjihkMZsiUkKhIAIfkECQoAAAAsAAAAABAAEAAAAzYIujIjK8pByJDMlFYvBoVjHA70GU7xSUJhmKtwHPAKzLO9HMaoKwJZ7Rf8AYPDDzKpZBqfvwQAIfkECQoAAAAsAAAAABAAEAAAAzMIumIlK8oyhpHsnFZfhYumCYUhDAQxRIdhHBGqRoKw0R8DYlJd8z0fMDgsGo/IpHI5TAAAIfkECQoAAAAsAAAAABAAEAAAAzIIunInK0rnZBTwGPNMgQwmdsNgXGJUlIWEuR5oWUIpz8pAEAMe6TwfwyYsGo/IpFKSAAAh+QQJCgAAACwAAAAAEAAQAAADMwi6IMKQORfjdOe82p4wGccc4CEuQradylesojEMBgsUc2G7sDX3lQGBMLAJibufbSlKAAAh+QQJCgAAACwAAAAAEAAQAAADMgi63P7wCRHZnFVdmgHu2nFwlWCI3WGc3TSWhUFGxTAUkGCbtgENBMJAEJsxgMLWzpEAACH5BAkKAAAALAAAAAAQABAAAAMyCLrc/jDKSatlQtScKdceCAjDII7HcQ4EMTCpyrCuUBjCYRgHVtqlAiB1YhiCnlsRkAAAOwAAAAAAAAAAAA==" />
          )}
          {error && <div className={"alert alert-danger"}>{error}</div>}
        </form>
      </div>
    );
  }
}

export default withRouter(CreateAccountForm);
