import React, { Component } from "react";
import { userService } from "../../../services/user";
import { withRouter } from "react-router";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import { ConfirmModal } from "react-bootstrap4-modal";
import validationFields from "../../../utils/validation/validationFields";
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
  ruleRunner(validationFields.category, requiredDropdown),
  ruleRunner(validationFields.primaryLanguage, requiredText)
];

class ProfileForm extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: {},
      showErrors: false,
      submitted: false,
      loading: false,
      errors: [],
      categoryOptions: [],
      countryOptions: [],
      titleOptions: [],
      genderOptions: [],
      disabilityOptions: [],
      ethnicityOptions: [],
      confirmResetVisible: false
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
        titleOptions: this.checkOptionsList(result[0]),
        genderOptions: this.checkOptionsList(result[1]),
        countryOptions: this.checkOptionsList(result[2]),
        categoryOptions: this.checkOptionsList(result[3]),
        ethnicityOptions: this.checkOptionsList(result[4]),
        disabilityOptions: this.checkOptionsList(result[5])
      });
    });

    userService.get().then(result => {
      var date = result.user_dateOfBirth;
      if (date) date = date.split("T")[0];
      this.setState({
        user: {
          title: result.user_title,
          firstName: result.firstname,
          lastName: result.lastname,
          email: result.email,
          nationality: result.nationality_country_id,
          residence: result.residence_country_id,
          gender: result.user_gender,
          ethnicity: result.user_ethnicity,
          disability: result.user_disability,
          affiliation: result.affiliation,
          department: result.department,
          category: result.user_category_id,
          dateOfBirth: date,
          primaryLanguage: result.user_primaryLanguage
        }
      });
    });
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

  deleteAccount = () => {
    userService.deleteAccount().then(
      response => {
        const { from } = this.props.location.state || {
          from: { pathname: "/" }
        };
        this.props.history.push(from);
      },
      error => this.setState({ error, loading: false })
    );
    if (this.props.logout) {
      this.props.logout();
    }
  };

  resetPassword = () => {
    userService.requestPasswordReset(this.state.user.email).then(response => {
      if (response.status === 201) {
        const { from } = { from: { pathname: "/" } };
        this.props.history.push(from);
      } else {
        this.setState({
          error: response.messsage,
          loading: false,
          confirmResetVisible: false
        });
      }
    });
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

    if (this.state.errors.$set.length > 0) return;

    this.setState({ loading: true });

    userService.update(this.state.user).then(
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
    const colClassEmailLanguageDob = createColClassName(12, 4, 4, 4);
    const {
      firstName,
      lastName,
      email,
      title,
      nationality,
      residence,
      ethnicity,
      gender,
      affiliation,
      department,
      disability,
      category,
      dateOfBirth,
      primaryLanguage
    } = this.state.user;

    const titleValue = this.getContentValue(this.state.titleOptions, title);
    const nationalityValue = this.getContentValue(
      this.state.countryOptions,
      nationality
    );
    const residenceValue = this.getContentValue(
      this.state.countryOptions,
      residence
    );
    const ethnicityValue = this.getContentValue(
      this.state.ethnicityOptions,
      ethnicity
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

    const { loading, errors, showErrors } = this.state;

    return (
      <div className="Profile">
        <form onSubmit={this.handleSubmit}>
          <p className="h5 text-center mb-4">Profile</p>
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
          </div>{" "}
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
              <FormSelect
                id={validationFields.ethnicity.name}
                options={this.state.ethnicityOptions}
                placeholder={validationFields.ethnicity.display}
                onChange={this.handleChangeDropdown}
                value={ethnicityValue}
                label={validationFields.ethnicity.display}
                description={validationFields.ethnicity.description}
              />
            </div>
            <div class={commonColClassName}>
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
              <button
                type="button"
                class="btn btn-primary Button"
                disabled={loading}
                onClick={() => this.setState({ confirmResetVisible: true })}
              >
                Reset password
              </button>
            </div>
            <div class={commonColClassName}>
              <button
                type="submit"
                class="btn btn-primary Button"
                disabled={loading}
              >
                {loading && (
                  <span
                    class="spinner-grow spinner-grow-sm"
                    role="status"
                    aria-hidden="true"
                  />
                )}
                Save profile
              </button>
            </div>
          </div>
          {errors && errors.$set && showErrors && this.getErrorMessages(errors)}
        </form>
        <ConfirmModal
          visible={this.state.confirmResetVisible}
          onOK={this.resetPassword}
          onCancel={() => this.setState({ confirmResetVisible: false })}
          okText={"Reset Password"}
          cancelText={"Cancel"}
        >
          <p>
            Are you sure? Click "Reset Password" to receive an email with a link
            to reset your password.
          </p>
        </ConfirmModal>
      </div>
    );
  }
}

export default withRouter(ProfileForm);
