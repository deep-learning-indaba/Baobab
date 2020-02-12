import React, { Component } from "react";
import { withRouter } from "react-router";
import { invitedGuestServices } from "../../../services/invitedGuests/invitedGuests.service";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import { createColClassName } from "../../../utils/styling/styling";
import "react-table/react-table.css";
import validationFields from "../../../utils/validation/validationFields";
import { run, ruleRunner } from "../../../utils/validation/ruleRunner";
import ReactTable from 'react-table';

import {
  requiredText,
  requiredDropdown,
  validEmail
} from "../../../utils/validation/rules.js";
import {
  getTitleOptions,
  getGenderOptions,
} from "../../../utils/validation/contentHelpers";

const baseFieldValidations = [
  ruleRunner(validationFields.email, validEmail),
  ruleRunner(validationFields.role, requiredDropdown)
];

const extraFieldValidations = [
  ruleRunner(validationFields.title, requiredDropdown),
  ruleRunner(validationFields.firstName, requiredText),
  ruleRunner(validationFields.lastName, requiredText),
  ruleRunner(validationFields.gender, requiredDropdown),
  ruleRunner(validationFields.affiliation, requiredText)
]

const MENTOR_ATTENDEE_CATEGORY_ID = 8;

class InvitedGuests extends Component {
  constructor(props) {
    super(props);
    this.state = {
      isLoading: true,
      isError: false,
      guestList: [],
      user: {},
      addedSucess: false,
      notFound: false,
      buttonClicked: false,
      conflict: false,
      error: "",
      errors: {},
      successMessage: "",
      adding: false,
      roleSearch: "all",
      searchTerm: ""
    };
  }
  getGuestList() {
    invitedGuestServices.getInvitedGuestList(this.props.event ? this.props.event.id : 0).then(result => {
      this.setState({
        loading: false,
        guestList: result.form,
        error: result.error,
        filteredList: result.form
      });
    });
  }

  checkOptionsList(optionsList) {
    if (Array.isArray(optionsList)) {
      return optionsList;
    } else return [];
  }

  componentDidMount() {
    this.setState({ loading: true }, () => this.getGuestList());
    Promise.all([
      getTitleOptions,
      getGenderOptions,
    ]).then(result => {
      this.setState({
        titleOptions: this.checkOptionsList(result[0]),
        genderOptions: this.checkOptionsList(result[1]),
      });
    });
  }

  runValidations = callback => {
    let fieldValidations = baseFieldValidations;
    if (this.state.notFound) {
      fieldValidations = fieldValidations.concat(extraFieldValidations);
    }
    let errorsForm = run(this.state.user, fieldValidations);
    if (!callback) {
      callback = () => { }
    }
    this.setState({ errors: { $set: errorsForm } }, callback);
  }

  handleChangeDropdown = (name, dropdown) => {
    this.setState(
      {
        user: {
          ...this.state.user,
          [name]: dropdown.value
        }
      },
      this.runValidations
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
        this.runValidations
      );
    };
  };

  convertToCsv = (guestList) => {
    var str = "NAME,EMAIL,AFFILIATION,ROLE\r\n";
    for (var i = 0; i < guestList.length; i++) {
      let fullname = guestList[i].user.user_title + " " + guestList[i].user.firstname + " " + guestList[i].user.lastname
      str += fullname + ',' + guestList[i].user.email + ',' + guestList[i].user.affiliation + ',' + guestList[i].role;
      str += "\r\n";
    }
    return str;
  };

  downloadCsv = () => {
    let csv = this.convertToCsv(this.state.guestList);
    var filename = "GuestList" + new Date().toDateString().split(" ").join("_") + ".csv";
    var csvData = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    if (navigator.msSaveBlob) {

      navigator.msSaveBlob(csvData, filename);

    } else {

      var link = document.createElement('a');
      link.href = window.URL.createObjectURL(csvData);
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };



  filterByName = field => {
    let searchList = this.state.guestList;

    let value = field.target.value.toLowerCase();
    var roleSearch = this.state.roleSearch;
    let tempList = searchList.filter((guest) => {
      let fullname = guest.user.user_title + " " + guest.user.firstname + " " + guest.user.lastname;
      return (fullname.toLowerCase().indexOf(value) > -1) && (roleSearch === "all" || guest.role === roleSearch)
    })
    this.setState({
      filteredList: tempList,
      searchTerm: value
    })
  };

  filterByRole = (name, dropdown) => {
    let searchList = this.state.guestList
    let tempList = searchList;
    var searchTerm = this.state.searchTerm;
    this.setState({
      roleSearch: dropdown.value
    });

    tempList = searchList.filter(function (guest) {
      let fullname = guest.user.user_title + " " + guest.user.firstname + " " + guest.user.lastname;
      if (guest.role === dropdown.value || dropdown.value === "all")
        if (searchTerm !== "") {
          if (fullname.toLowerCase().indexOf(searchTerm) > -1) {
            return guest;
          }
        }
        else {
          return guest;
        }
      return false;
    })
    this.setState({
      filteredList: tempList,
    })
  };
  getSearchRoles(roles) {
    let temp = roles.slice();
    let role = { value: "all", label: "All" };
    temp.push(role);
    return temp;
  }

  handleResponse = response => {
    if (response.msg === "succeeded") {
      this.setState({
        addedSucess: true,
        conflict: false,
        notFound: false,
        successMessage: "Added " + response.response.data.fullname + " to the guest list",
        user: {},
        showErrors: false,
        adding: false
      }, this.getGuestList);
    } else if (response.msg === "404") {
      this.setState({
        addedSucess: false,
        notFound: true,
        conflict: false,
        successMessage: "",
        adding: false
      }, this.getGuestList);
    } else if (response.msg === "409") {
      this.setState({
        notFound: false,
        addedSucess: false,
        conflict: true,
        user: {},
        successMessage: "",
        showErrors: false,
        adding: false
      }, this.getGuestList);
    } else {
      this.setState({
        error: response.error,
        adding: false
      });
    }
  }

  buttonSubmit() {
    this.runValidations(() => {
      let errors = this.state.errors;
      if (errors && errors.$set && errors.$set.length > 0) {
        this.setState({ showErrors: true });
        return;
      }

      this.setState({ adding: true });
      invitedGuestServices
        .addInvitedGuest(this.state.user.email, this.props.event ? this.props.event.id : 0, this.state.user.role)
        .then(resp => this.handleResponse(resp));
    });
  }

  submitCreate = () => {
    this.runValidations(() => {
      let errors = this.state.errors;
      if (errors && errors.$set && errors.$set.length > 0) {
        this.setState({ showErrors: true });
        return;
      }
      const user = {
        ...this.state.user,
        category: MENTOR_ATTENDEE_CATEGORY_ID
      };

      this.setState({ adding: true });
      invitedGuestServices
        .createInvitedGuest(user, this.props.event ? this.props.event.id : 0, user.role)
        .then(resp => this.handleResponse(resp));
    });
  }

  getError = id => {
    if (!this.state.showErrors) {
      return "";
    }

    if (this.state.errors && this.state.errors.$set && this.state.errors.$set.length > 0) {
      let errorMessage = this.state.errors.$set.find(e => e[id]);
      if (errorMessage) {
        return Object.values(errorMessage)[0];
      }
      return "";
    }
    return "";
  }

  // TODO change Baobab to [event]
  render() {
    const threeColClassName = createColClassName(12, 4, 4, 4);  //xs, sm, md, lg

    const { loading, error } = this.state;
    const roleOptions = invitedGuestServices.getRoles()
    const searchRoleOptions = this.getSearchRoles(roleOptions);

    if (loading) {
      return (
        <div class="d-flex justify-content-center">
          <div class="spinner-border" role="status">
            <span class="sr-only">Loading...</span>
          </div>
        </div>
      );
    }

    const columns = [
      {
        id: "user",
        Header: <div className="invitedguest-fullname">Full-Name</div>,
        accessor: u => <div className="invitedguest-fullname">{u.user.user_title + " " + u.user.firstname + " " + u.user.lastname}</div>,
        minWidth: 150
      },
      {
        id: "email",
        Header: <div className="invitedguest-email">Email</div>,
        accessor: u => u.user.email
      },
      {
        id: "affiliation",
        Header: <div className="invitedguest-affiliation">Affiliation</div>,
        accessor: u => u.user.affiliation
      },
      {
        id: "role",
        Header: <div className="invitedguest-role">Role</div>,
        accessor: u => u.role
      },
    ];

    return (
      <div className="InvitedGuests container-fluid pad-top-30-md">
        {error &&
          <div className={"alert alert-danger alert-container"}>
            {JSON.stringify(error)}
          </div>}

        <div class="card no-padding-h">
          <p className="h5 text-center mb-4 ">Invited Guests</p>
          <div className="row">
            <div className={threeColClassName}>
              <FormTextBox
                id="s"
                type="text"
                placeholder="Search"
                onChange={this.filterByName}
                label="Filter by name"
                name=""
                value={this.state.searchTerm}
              />
            </div>

            <div class={threeColClassName}>
              <FormSelect
                options={searchRoleOptions}
                id="RoleFilter"
                placeholder="search"
                onChange={this.filterByRole}
                label="Filter by role"
                defaultValue={this.state.roleSearch || "all"}
              />
            </div>

          </div>
          {
            this.state.guestList && this.state.guestList.length > 0 &&
            <ReactTable
              data={this.state.filteredList}
              columns={columns}
              minRows={0} />
          }

          {
            (!this.state.guestList || this.state.guestList.length === 0) &&
            <div class="alert alert-danger alert-container">
              No invited guests
              </div>
          }
          <div className="col-12">
            <button
              className="pull-right link-style"
              onClick={() => this.downloadCsv()}>
              Download csv
              </button>
          </div>
        </div>

        {this.state.addedSucess && (
          <div class="card flat-card success">
            {this.state.successMessage}
          </div>
        )}

        {this.state.addedSucess === false && this.state.conflict && (
          <div class="card flat-card conflict">
            Invited guest with this email already exists.
          </div>
        )}

        <form>
          <div class="card">
            <p className="h5 text-center mb-4">Add Guest</p>
            <div class="row">
              <div class={threeColClassName}>
                <FormTextBox
                  id={validationFields.email.name}
                  type="email"
                  placeholder={validationFields.email.display}
                  onChange={this.handleChange(validationFields.email)}
                  label={validationFields.email.display}
                  showError={this.getError(validationFields.email.name)}
                  errorText={this.getError(validationFields.email.name)}
                  value={this.state.user[validationFields.email.name] || ""}
                />
              </div>

              <div class={threeColClassName}>
                <FormSelect
                  options={roleOptions}
                  id={validationFields.role.name}
                  placeholder={validationFields.role.display}
                  onChange={this.handleChangeDropdown}
                  label={validationFields.role.display}
                  showError={this.getError(validationFields.role.name)}
                  errorText={this.getError(validationFields.role.name)}
                  defaultValue={this.state.user[validationFields.role.name] || ""}
                  value={this.state.user[validationFields.role.name] || ""}
                />
              </div>
              <div class={threeColClassName}>
                {!this.state.notFound &&
                  <button
                    type="button"
                    class="btn btn-primary stretched margin-top-32"
                    onClick={() => this.buttonSubmit()}
                    disabled={this.state.adding}
                  >
                    {this.state.adding && (
                      <span
                        class="spinner-grow spinner-grow-sm"
                        role="status"
                        aria-hidden="true"
                      />
                    )}
                    Add
                  </button>
                }
                {!this.state.addedSucess && this.state.notFound &&
                  <span className="text-warning not-found">
                    User does not exist in Baobab, please add these details:
                  </span>
                }
              </div>
            </div>

            {!this.state.addedSucess && this.state.notFound &&
              <div>
                <div class="row">
                  <div className={threeColClassName}>
                    <FormSelect
                      options={this.state.titleOptions}
                      id={validationFields.title.name}
                      placeholder={validationFields.title.display}
                      onChange={this.handleChangeDropdown}
                      label={validationFields.title.display}
                      showError={this.getError(validationFields.title.name)}
                      errorText={this.getError(validationFields.title.name)}
                      defaultValue={this.state.user[validationFields.title.name] || ""}
                      value={this.state.user[validationFields.title.name] || ""}
                    />
                  </div>
                  <div className={threeColClassName}>
                    <FormTextBox
                      id={validationFields.firstName.name}
                      type="text"
                      placeholder={validationFields.firstName.display}
                      onChange={this.handleChange(validationFields.firstName)}
                      label={validationFields.firstName.display}
                      showError={this.getError(validationFields.firstName.name)}
                      errorText={this.getError(validationFields.firstName.name)}
                      value={this.state.user[validationFields.firstName.name] || ""}
                    />
                  </div>
                  <div className={threeColClassName}>
                    <FormTextBox
                      id={validationFields.lastName.name}
                      type="text"
                      placeholder={validationFields.lastName.display}
                      onChange={this.handleChange(validationFields.lastName)}
                      label={validationFields.lastName.display}
                      showError={this.getError(validationFields.lastName.name)}
                      errorText={this.getError(validationFields.lastName.name)}
                      value={this.state.user[validationFields.lastName.name] || ""}
                    />
                  </div>
                </div>
                <div class="row">
                  <div className={threeColClassName}>
                    <FormSelect
                      options={this.state.genderOptions}
                      id={validationFields.gender.name}
                      placeholder={validationFields.gender.display}
                      onChange={this.handleChangeDropdown}
                      label={validationFields.gender.display}
                      showError={this.getError(validationFields.gender.name)}
                      errorText={this.getError(validationFields.gender.name)}
                      defaultValue={this.state.user[validationFields.gender.name] || ""}
                      value={this.state.user[validationFields.gender.name] || ""}
                    />
                  </div>
                  <div className={threeColClassName}>
                    <FormTextBox
                      id={validationFields.affiliation.name}
                      type="text"
                      placeholder={validationFields.affiliation.display}
                      onChange={this.handleChange(validationFields.affiliation)}
                      label={validationFields.affiliation.display}
                      showError={this.getError(validationFields.affiliation.name)}
                      errorText={this.getError(validationFields.affiliation.name)}
                      value={this.state.user[validationFields.affiliation.name] || ""}
                    />
                  </div>
                  <div className={threeColClassName}>
                    <button
                      type="button"
                      class="btn btn-primary stretched margin-top-32"
                      onClick={() => this.submitCreate()}
                      disabled={this.state.adding}
                    >
                      {this.state.adding && (
                        <span
                          class="spinner-grow spinner-grow-sm"
                          role="status"
                          aria-hidden="true"
                        />
                      )}
                      Create Invited Guest
                    </button>
                  </div>
                </div>
              </div>
            }

          </div>
        </form>
      </div>
    );
  }
}

export default withRouter(InvitedGuests);
