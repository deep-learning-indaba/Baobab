import React, { Component } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import FormTextBox from "../../../components/form/FromTextBox";
import FormSelect from "../../../components/form/FormSelect";
import validationFields from "../../../utils/validation/validationFields";
import { default as ReactSelect } from "react-select";
import {
  titleOptions,
  getCounties,
  genderOptions
} from "../../../utils/validation/contentHelpers";
import { createColClassName } from "../../../utils/styling/styling";

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
    const xs = 12;
    const sm = 6;
    const md = 6;
    const lg = 6;
    const commonColClassName = createColClassName(xs, sm, md, lg);
    const colClassNameTitle = createColClassName(12, 4, 2, 2);
    const colClassNameSurname = createColClassName(12, 4, 5, 5);
    const {
      firstName,
      lastName,
      email,
      title,
      password,
      confirmPassword,
      loading,
      error,
      nationality,
      nationalityId,
      residence,
      residenceId,
      ethnicity,
      gender,
      affiliation,
      department,
      disability
    } = this.state;
    return (
      <div className="CreateAccount">
        <form onSubmit={this.handleSubmit}>
          <p className="h5 text-center mb-4">Create Account</p>
          <div class="row">
            <div class={colClassNameTitle}>
              <FormSelect
                options={titleOptions}
                id={validationFields.title.name}
                placeholder={validationFields.title.display}
                onChange={this.handleChange(validationFields.title)}
                value={title}
                label={validationFields.title.display}
              />
            </div>
            <div class={colClassNameSurname}>
              <FormTextBox
                id={validationFields.firstName.name}
                type="text"
                placeholder={validationFields.firstName.display}
                onChange={this.handleChange(validationFields.firstName)}
                value={firstName}
                label={validationFields.firstName.display}
              />
            </div>
            <div class={colClassNameSurname}>
              <FormTextBox
                id={validationFields.lastName.name}
                type="text"
                placeholder={validationFields.lastName.display}
                onChange={this.handleChange(validationFields.lastName)}
                value={lastName}
                label={validationFields.lastName.display}
              />
            </div>
          </div>
          <FormTextBox
            id={validationFields.email.name}
            type="email"
            placeholder={validationFields.email.display}
            onChange={this.handleChange(validationFields.email)}
            value={email}
            label={validationFields.email.display}
          />
          <div class="row">
            <div class={commonColClassName}>
              <FormSelect
                options={getCounties()}
                id={validationFields.nationality.name}
                placeholder={validationFields.nationality.display}
                onChange={this.handleChange(validationFields.nationality)}
                value={nationality}
                label={validationFields.nationality.display}
              />
            </div>
            <div class={commonColClassName}>
              <FormSelect
                options={getCounties()}
                id={validationFields.residence.name}
                placeholder={validationFields.residence.display}
                onChange={this.handleChange(validationFields.residence)}
                value={residence}
                label={validationFields.residence.display}
              />
            </div>
          </div>
          <div class="row">
            <div class={commonColClassName}>
              <FormTextBox
                id={validationFields.ethnicity.name}
                type="text"
                placeholder={validationFields.ethnicity.display}
                onChange={this.handleChange(validationFields.ethnicity)}
                value={ethnicity}
                label={validationFields.ethnicity.display}
              />
            </div>
            <div class={commonColClassName}>
              <FormSelect
                options={genderOptions}
                id={validationFields.gender.name}
                placeholder={validationFields.gender.display}
                onChange={this.handleChange(validationFields.gender)}
                value={gender}
                label={validationFields.gender.display}
              />
            </div>
          </div>
          <div class="row">
            <div class={commonColClassName}>
              <FormTextBox
                id={validationFields.affiliation.name}
                type="text"
                placeholder={validationFields.affiliation.display}
                onChange={this.handleChange(validationFields.affiliation)}
                value={affiliation}
                label={validationFields.affiliation.display}
              />
            </div>
            <div class={commonColClassName}>
              <FormTextBox
                id={validationFields.department.name}
                type="text"
                placeholder={validationFields.department.display}
                onChange={this.handleChange(validationFields.department)}
                value={department}
                label={validationFields.department.display}
              />
            </div>
          </div>
          <FormTextBox
            id={validationFields.disability.name}
            type="text"
            placeholder={validationFields.disability.display}
            onChange={this.handleChange(validationFields.disability)}
            value={disability}
            label={validationFields.disability.display}
          />
          <div class="row">
            <div class={commonColClassName}>
              <FormTextBox
                id={validationFields.password.name}
                type="password"
                placeholder={validationFields.password.display}
                onChange={this.handleChange(validationFields.password)}
                value={password}
                label={validationFields.password.display}
              />
            </div>
            <div class={commonColClassName}>
              <FormTextBox
                id={validationFields.confirmPassword.name}
                type="password"
                placeholder={validationFields.confirmPassword.display}
                onChange={this.handleChange(validationFields.confirmPassword)}
                value={confirmPassword}
                label={validationFields.confirmPassword.display}
              />
            </div>
          </div>
          <button
            type="submit"
            class="btn btn-primary"
            disabled={!this.validateForm() || loading}
          >
            Sign Up
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
