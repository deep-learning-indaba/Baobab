import React, { Component } from "react";
import { invitedGuestServices } from "../../../services/invitedGuests/invitedGuests.service";
import { withRouter } from "react-router";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import validationFields from "../../../utils/validation/validationFields";
import {
  getTitleOptions,
} from "../../../utils/validation/contentHelpers";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import {
  requiredText,
  requiredDropdown,
  validEmail,
} from "../../../utils/validation/rules.js";
import { createColClassName } from "../../../utils/styling/styling";

const fieldValidations = [
  ruleRunner(validationFields.title, requiredDropdown),
  ruleRunner(validationFields.firstName, requiredText),
  ruleRunner(validationFields.lastName, requiredText),
  ruleRunner(validationFields.email, validEmail),
];

class creatreInvitedGuestComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: {
        email: props.email || null,
        role: props.role || null
      },
      submitted: false,
      errors: [],
      titleOptions: [],
      error: "",
      created: false,
      conflict: false
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
    ]).then(result => {
      this.setState({
        titleOptions: this.checkOptionsList(result[0]),
      });
    });
  }

  validateForm() {
    return (this.state.user && this.state.user.email && this.state.user.email.length > 0);
  }

  handleChangeDropdown = (name, dropdown) => {
    this.setState(
      {
        user: {
          ...this.state.user,
          [name]: dropdown.value
        }
      },
      function () {
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
        function () {
          let errorsForm = run(this.state.user, fieldValidations);
          this.setState({ errors: { $set: errorsForm } });
        }
      );
    };
  };

  handleSubmit = event => {
    event.preventDefault();
    this.setState({ submitted: true });

    if (
      this.state.errors &&
      this.state.errors.$set &&
      this.state.errors.$set.length > 0
    )
      return;

    //TODO review this workflow, it seems dodgy. 
    //createInvitedGuest always returns 400 (no role). Then addInvitedGuest creates the invitedguest.
    invitedGuestServices
      .createInvitedGuest(this.state.user, this.props.event ? this.props.event.id : 0)
      .then(user => {
        this.setState({
          created: true
        });
        if (user.msg === "409") {
          this.setState({
            conflict: true
          });
        } else if (this.state.created === true) {
          invitedGuestServices.addInvitedGuest(
            this.state.user.email,
            this.props.event ? this.props.event.id : 0,
            this.state.user.role
          );
          this.props.history.push("/invitedGuests");
        }
      });
  };

  render() {
    const xs = 12;
    const sm = 4;
    const md = 4;
    const lg = 4;
    const commonColClassName = createColClassName(xs, sm, md, lg);
    const {
      firstName,
      lastName,
      email,
      title,
    } = this.state.user;

    const roleOptions = invitedGuestServices.getRoles();

    const titleValue = this.getContentValue(this.state.titleOptions, title);

    return (
      <div className="CreateAccount">
        <form onSubmit={this.handleSubmit}>
          <p className="h5 text-center mb-4">Create Guest</p>
          <div class="row">
            <div class={commonColClassName}>
              <FormSelect
                options={this.state.titleOptions}
                id={validationFields.title.name}
                placeholder={validationFields.title.display}
                onChange={this.handleChangeDropdown}
                value={titleValue}
                label={validationFields.title.display}
              />
            </div>
            <div class={commonColClassName}>
              <FormTextBox
                id={validationFields.firstName.name}
                type="text"
                placeholder={validationFields.firstName.display}
                onChange={this.handleChange(validationFields.firstName)}
                value={firstName}
                label={validationFields.firstName.display}
              />
            </div>
            <div class={commonColClassName}>
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
            <div class={commonColClassName}>
              <FormTextBox
                id={validationFields.email.name}
                type="email"
                placeholder={validationFields.email.display}
                onChange={this.handleChange(validationFields.email)}
                value={email}
                label={validationFields.email.display}
              />
            </div>
            <div class={commonColClassName}>
              <FormSelect
                defaultValue={this.state.user.role}
                options={roleOptions}
                id={"role"}
                onChange={this.handleChangeDropdown}
                label={"Role"}
              />
            </div>
          </div>
          <button
            type="submit"
            class="btn btn-primary"
            disabled={!this.validateForm()}
          >
            Create guest
          </button>
          {this.state.conflict && (
            <div class="alert alert-danger">Email is already taken</div>
          )}
        </form>
      </div>
    );
  }
}

export default withRouter(creatreInvitedGuestComponent);
