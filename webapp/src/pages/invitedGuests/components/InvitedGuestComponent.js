import React, { Component } from "react";
import { withRouter } from "react-router";
import { invitedGuestServices } from "../../../services/invitedGuests/invitedGuests.service";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import { createColClassName } from "../../../utils/styling/styling";
import "react-table/react-table.css";
import validationFields from "../../../utils/validation/validationFields";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import {
  requiredText,
  requiredDropdown,
  validEmail
} from "../../../utils/validation/rules.js";

const fieldValidations = [ruleRunner(validationFields.email, validEmail)];

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

class InvitedGuests extends Component {
  constructor(props) {
    super(props);
    this.state = {
      isLoading: true,
      isError: false,
      email: "",
      guestList: [],
      role: "",
      addedSucess: false,
      notFound: false,
      buttonClicked: false,
      conflict: false
    };
  } 
  getGuestList() {
    this.setState({ loading: true });
    invitedGuestServices.getInvitedGuestList(DEFAULT_EVENT_ID).then(result => {
      this.setState({
        loading: false,
        guestList: result.form,
        error: result.error
      });
    });
  }

  componentDidMount() {
    this.getGuestList();
  }

  handleChangeDropdown = (name, dropdown) => {
    this.setState({
      [name]: dropdown.value
    });
  };
  buttonSubmit() {
    invitedGuestServices
      .addInvitedGuest(this.state.email, DEFAULT_EVENT_ID, this.state.role)
      .then(response => {
        if (response.msg === "succeeded") {
          this.getGuestList();
          this.setState({
            addedSucess: true,
            conflict: false,
            notFound: false
          });
        } else if (response.msg === "404") {
          this.setState({
            addedSucess: false,
            notFound: true,
            conflict: false
          });
        } else if (response.msg === "409") {
          this.setState({
            notFound: false,
            addedSucess: false,
            conflict: true
          });
        }
      });
  }
  handleChange = field => {
    return event => {
      this.setState({
        [field.name]: event.target.value
      });
    };
  };

  render() {
    const xs = 12;
    const sm = 4;
    const md = 4;
    const lg = 4;
    const commonColClassName = createColClassName(xs, sm, md, lg);
    const colClassEmailLanguageDob = createColClassName(12, 4, 4, 4);
    const { loading } = this.state;
    const roleOptions = [
      { value: "Speaker", label: "Speaker" },
      { value: "Guest", label: "Guest" },
      { value: "Mentor", label: "Mentor" },
      { value: "Friend of the Indaba", label: "Friend of the Indaba" },
      { value: "Organiser", label: "Organiser" }
    ];
    let lastGuest;
    if (this.state.guestList !== null) {
      lastGuest = this.state.guestList[this.state.guestList.length - 1];
    }

    if (loading) {
      return (
        <div class="d-flex justify-content-center">
          <div class="spinner-border" role="status">
            <span class="sr-only">Loading...</span>
          </div>
        </div>
      );
    }

    return (
      <div className="InvitedGuests container-fluid pad-top-30-md">
        <div class="card no-padding-h">
          <p className="h5 text-center mb-1 ">Invited Guests</p>
          <div class="responsive-table">
            {this.state.guestList !== null &&
            this.state.guestList.length > 0 ? (
              <table cellPadding={5} className="stretched round-table">
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Lastname</th>
                    <th scope="col">Email</th>
                    <th scope="col">Role</th>
                    <th scope="col">Department</th>
                  </tr>
                </thead>
                {this.state.guestList.map(user => (
                  <tbody className="white-background" key={user.email}>
                    <tr className="font-size-12">
                      <td>{user.user.firstname}</td>
                      <td>{user.user.lastname}</td>
                      <td>{user.user.email}</td>
                      <td>{user.role}</td>
                      <td>{user.user.department}</td>
                    </tr>
                  </tbody>
                ))}
              </table>
            ) : (
              <div class="alert alert-danger">No invited guests</div>
            )}
          </div>
        </div>

        {this.state.addedSucess ? (
          <div class="card flat-card success">
            {" "}
            Successfully added {lastGuest.user.firstname}{" "}
            {lastGuest.user.lastname}
          </div>
        ) : this.state.addedSucess === false && this.state.notFound ? (
          <div class="alert alert-danger">
            User does not exist
            <a
              href={
                "/invitedGuests/create?email=" +
                this.state.email +
                "&event=" +
                DEFAULT_EVENT_ID +
                "&role=" +
                this.state.role
              }
            >
              {" "}
              Click here to create
            </a>
          </div>
        ) : this.state.addedSucess === false && this.state.conflict ? (
          <div class="card flat-card conflict">
            Invited guest with this email already exists.
          </div>
        ) : null}

        <form>
          <div class="card">
            <p className="h5 text-center mb-4">Add Guest</p>
            <div class="row">
              <div class={colClassEmailLanguageDob}>
                <FormTextBox
                  id={validationFields.email.name}
                  type="email"
                  placeholder={validationFields.email.display}
                  onChange={this.handleChange(validationFields.email)}
                  label={validationFields.email.display}
                />
              </div>

              <div class={commonColClassName}>
                <FormSelect
                  options={roleOptions}
                  id={"role"}
                  onChange={this.handleChangeDropdown}
                  label={"Select role"}
                />
              </div>
              <div class={commonColClassName}>
                <button
                  type="button"
                  class="btn btn-primary stretched margin-top-32"
                  onClick={() => this.buttonSubmit()}
                >
                  Create invited guest
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    );
  }
}

export default withRouter(InvitedGuests);
