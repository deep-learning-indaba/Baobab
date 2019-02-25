import React, { Component } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import FormTextBox from "../../../components/form/FromTextBox";
import FormSelect from "../../../components/form/FormSelect";
import validationFields from "../../../utils/validation/validationFields";
import { default as ReactSelect } from "react-select";
import {
  getTitleOptions,
  getCounties,
  getGenderOptions,
  getCategories,
  getDisabilityOptions,
  getEthnicityOptions
} from "../../../utils/validation/contentHelpers";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import {
  requiredText,
  requiredDropdown,
  validEmail
} from "../../../utils/validation/rules.js";
import { createColClassName } from "../../../utils/styling/styling";

const fieldValidations = [
  ruleRunner(validationFields.title, requiredDropdown),
  ruleRunner(validationFields.firstName, requiredText),
  ruleRunner(validationFields.lastName, requiredText),
  ruleRunner(validationFields.email, validEmail),
  ruleRunner(validationFields.nationality, requiredDropdown),
  ruleRunner(validationFields.residence, requiredDropdown),
  ruleRunner(validationFields.ethnicity, requiredText),
  ruleRunner(validationFields.gender, requiredDropdown),
  ruleRunner(validationFields.affiliation, requiredText),
  ruleRunner(validationFields.department, requiredText),
  ruleRunner(validationFields.disability, requiredText),
  ruleRunner(validationFields.password, requiredText),
  ruleRunner(validationFields.confirmPassword, requiredText),
  ruleRunner(validationFields.category, requiredDropdown)
];

class CreateAccountForm extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: {
        email: "",
        password: "",
        confirmPassword: ""
      },
      showErrors: false,
      submitted: false,
      loading: false,
      errors: [],
      categoryOptions: [],
      countryOptions: [],
      titleOptions: [],
      genderOptions: [],
      disabilityOptions: [],
      ethnicityOptions: []
    };
  }

  componentWillMount() {
    Promise.all([
      getTitleOptions,
      getGenderOptions,
      getCounties,
      getCategories,
      getEthnicityOptions,
      getDisabilityOptions
    ]).then(result => {
      this.setState({
        titleOptions: result[0],
        genderOptions: result[1],
        countryOptions: result[2],
        categoryOptions: result[3],
        ethnicityOptions: result[4],
        disabilityOptions: result[5]
      });
    });
  }

  validateForm() {
    return (
      this.state.user.email.length > 0 &&
      this.state.user.password.length > 0 &&
      this.state.user.confirmPassword.length > 0
    );
  }

  handleChangeDropdown = (name, dropdown) => {
    this.setState(
      {
        user: {
          ...this.state.user,
          [name]: dropdown.value
        }
      },
      function() {
        let errorsForm = run(this.state.user, fieldValidations);
        this.setState({ errors: { $set: errorsForm } });
      }
    );
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
        function() {
          let errorsForm = run(this.state.user, fieldValidations);
          this.setState({ errors: { $set: errorsForm } });
        }
      );
    };
  };

  handleSubmit = event => {
    event.preventDefault();
    this.setState({ submitted: true, showErrors: true });

    if (this.state.user.password != this.state.user.confirmPassword) {
      this.state.errors.$set.push({ passwords: "Passwords do not match" });
    }
    if (this.state.errors.$set.length > 0) return;

    this.setState({ loading: true });

    userService.create(this.state.user).then(
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
      nationality,
      residence,
      ethnicity,
      gender,
      affiliation,
      department,
      disability,
      category
    } = this.state.user;

    const { loading, errors, showErrors } = this.state;

    return (
      <div className="CreateAccount">
        <form onSubmit={this.handleSubmit}>
          <p className="h5 text-center mb-4">Create Account</p>
          <div class="row">
            <div class={colClassNameTitle}>
              <FormSelect
                options={this.state.titleOptions}
                id={validationFields.title.name}
                placeholder={validationFields.title.display}
                onChange={this.handleChangeDropdown}
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
                options={this.state.countryOptions}
                id={validationFields.nationality.name}
                placeholder={validationFields.nationality.display}
                onChange={this.handleChangeDropdown}
                value={nationality}
                label={validationFields.nationality.display}
              />
            </div>
            <div class={commonColClassName}>
              <FormSelect
                options={this.state.countryOptions}
                id={validationFields.residence.name}
                placeholder={validationFields.residence.display}
                onChange={this.handleChangeDropdown}
                value={residence}
                label={validationFields.residence.display}
              />
            </div>
          </div>
          <div class="row">
            <div class={commonColClassName}>
              <FormSelect
                id={validationFields.ethnicity.name}
                options={this.state.ethnicityOptions}
                placeholder={validationFields.ethnicity.display}
                onChange={this.handleChangeDropdown}
                value={ethnicity}
                label={validationFields.ethnicity.display}
              />
            </div>
            <div class={commonColClassName}>
              <FormSelect
                options={this.state.genderOptions}
                id={validationFields.gender.name}
                placeholder={validationFields.gender.display}
                onChange={this.handleChangeDropdown}
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
          <div class="row">
            <div class={commonColClassName}>
              <FormSelect
                options={this.state.disabilityOptions}
                id={validationFields.disability.name}
                placeholder={validationFields.disability.display}
                onChange={this.handleChangeDropdown}
                value={disability}
                label={validationFields.disability.display}
              />
            </div>
            <div class={commonColClassName}>
              <FormSelect
                options={this.state.categoryOptions}
                id={validationFields.category.name}
                placeholder={validationFields.category.display}
                onChange={this.handleChangeDropdown}
                value={category}
                label={validationFields.category.display}
              />
            </div>
          </div>
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
          {errors && errors.$set && showErrors && this.getErrorMessages(errors)}
        </form>
      </div>
    );
  }
}

export default withRouter(CreateAccountForm);
