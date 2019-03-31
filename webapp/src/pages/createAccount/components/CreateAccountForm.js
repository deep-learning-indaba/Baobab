import React, { Component } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import validationFields from "../../../utils/validation/validationFields";
import {
  getTitleOptions,
  getCounties,
  getGenderOptions,
  getCategories,
  getDisabilityOptions
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
  ruleRunner(validationFields.gender, requiredDropdown),
  ruleRunner(validationFields.affiliation, requiredText),
  ruleRunner(validationFields.department, requiredText),
  ruleRunner(validationFields.disability, requiredText),
  ruleRunner(validationFields.password, requiredText),
  ruleRunner(validationFields.confirmPassword, requiredText),
  ruleRunner(validationFields.category, requiredDropdown),
  ruleRunner(validationFields.primaryLanguage, requiredText)
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
      error: "",
      created: false
    };
  }

  getContentValue(options, value) {
    if (options && options.filter) {
      return options.filter(option => {
        return option.value === value;
      });
    } else return null;
  }

  checkOptionsList(optionsList) {
    if (Array.isArray(optionsList)) {
      return optionsList;
    } else return [];
  }

  componentWillMount() {
    Promise.all([
      getTitleOptions,
      getGenderOptions,
      getCounties,
      getCategories,
      getDisabilityOptions
    ]).then(result => {
      this.setState({
        titleOptions: this.checkOptionsList(result[0]),
        genderOptions: this.checkOptionsList(result[1]),
        countryOptions: this.checkOptionsList(result[2]),
        categoryOptions: this.checkOptionsList(result[3]),
        disabilityOptions: this.checkOptionsList(result[4])
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
        this.setState({
          loading: false,
          created: true
        });
      },
      error =>
        this.setState({
          error:
            error.response && error.response.data
              ? error.response.data.message
              : error.message,
          loading: false
        })
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
    const colClassNameTitle = createColClassName(12, 3, 2, 2);
    const colClassNameSurname = createColClassName(12, 3, 4, 4);
    const colClassEmailLanguageDob = createColClassName(12, 4, 4, 4);
    const {
      firstName,
      lastName,
      email,
      title,
      nationality,
      residence,
      gender,
      affiliation,
      department,
      disability,
      category,
      password,
      confirmPassword,
      dateOfBirth,
      primaryLanguage
    } = this.state.user;

    const { loading, errors, showErrors, error, created } = this.state;

    if (created) {
      return (
        <div className="CreateAccount">
          <p className="h5 text-center mb-4">Create Account</p>
          <p className="account-created">
            Your Baobab account has been created, but before you can use it, we
            need to verify your email address. Please check your email (and spam
            folder) for a message containing a link to verify your email
            address.
          </p>
        </div>
      );
    }

    const titleValue = this.getContentValue(this.state.titleOptions, title);
    const nationalityValue = this.getContentValue(
      this.state.countryOptions,
      nationality
    );
    const residenceValue = this.getContentValue(
      this.state.countryOptions,
      residence
    );
    const genderValue = this.getContentValue(this.state.genderOptions, gender);
    const categoryValue = this.getContentValue(
      this.state.categoryOptions,
      category
    );
    const disabilityValue = this.getContentValue(
      this.state.disabilityOptions,
      disability
    );

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
                value={titleValue}
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
            <div class={colClassNameTitle}>
              <FormSelect
                options={this.state.genderOptions}
                id={validationFields.gender.name}
                placeholder={validationFields.gender.display}
                onChange={this.handleChangeDropdown}
                value={genderValue}
                label={validationFields.gender.display}
              />
            </div>
          </div>
          <div class="row">
            <div class={colClassEmailLanguageDob}>
              <FormTextBox
                id={validationFields.email.name}
                type="email"
                placeholder={validationFields.email.display}
                onChange={this.handleChange(validationFields.email)}
                value={email}
                label={validationFields.email.display}
              />
            </div>
            <div class={colClassEmailLanguageDob}>
              <FormTextBox
                id={validationFields.dateOfBirth.name}
                type="date"
                placeholder={validationFields.dateOfBirth.display}
                onChange={this.handleChange(validationFields.dateOfBirth)}
                value={dateOfBirth}
                label={validationFields.dateOfBirth.display}
              />
            </div>
            <div class={colClassEmailLanguageDob}>
              <FormTextBox
                id={validationFields.primaryLanguage.name}
                type="text"
                placeholder={validationFields.primaryLanguage.display}
                onChange={this.handleChange(validationFields.primaryLanguage)}
                value={primaryLanguage}
                label={validationFields.primaryLanguage.display}
              />
            </div>
          </div>
          <div class="row">
            <div class={commonColClassName}>
              <FormSelect
                options={this.state.countryOptions}
                id={validationFields.nationality.name}
                placeholder={validationFields.nationality.display}
                onChange={this.handleChangeDropdown}
                value={nationalityValue}
                label={validationFields.nationality.display}
              />
            </div>
            <div class={commonColClassName}>
              <FormSelect
                options={this.state.countryOptions}
                id={validationFields.residence.name}
                placeholder={validationFields.residence.display}
                onChange={this.handleChangeDropdown}
                value={residenceValue}
                label={validationFields.residence.display}
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
                description={validationFields.affiliation.description}
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
                description={validationFields.department.description}
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
                value={disabilityValue}
                label={validationFields.disability.display}
                description={validationFields.disability.description}
              />
            </div>
            <div class={commonColClassName}>
              <FormSelect
                options={this.state.categoryOptions}
                id={validationFields.category.name}
                placeholder={validationFields.category.display}
                onChange={this.handleChangeDropdown}
                value={categoryValue}
                label={validationFields.category.display}
                description={validationFields.category.description}
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
            {loading && (
              <span
                class="spinner-grow spinner-grow-sm"
                role="status"
                aria-hidden="true"
              />
            )}
            Sign Up
          </button>
          {errors && errors.$set && showErrors && this.getErrorMessages(errors)}
          {error && <div class="alert alert-danger">{error}</div>}
        </form>
      </div>
    );
  }
}

export default withRouter(CreateAccountForm);
