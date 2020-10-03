// TODO: ADD TRANSLATION

import React, { Component } from "react";
import { withRouter } from "react-router";
import "react-table/react-table.css";
import ReactTable from 'react-table';
import FormTextBox from "../../../components/form/FormTextBox";
import { registrationAdminService } from "../../../services/registration/registration.admin.service";

class RegistrationAdminComponent extends Component {
  constructor(props) {
    super(props);
    this.state = {
      isLoading: true,
      unconfirmedList: [],
      filteredList: [],
      error: "",
      searchTerm: "",
      loading: false,
      confirming: false,
      confirmError: ""
    };
  }

  getUnconfirmed = () => {
    registrationAdminService.getUnconfirmed(this.props.event ? this.props.event.id : 0).then(response => {
      this.setState({
        unconfirmedList: response.data,
        error: response.error,
        loading: false
      }, () => this.filterList());
    })
  }

  onConfirm = registrationId => {
    this.setState({ confirming: true }, () => {
      registrationAdminService.confirm(registrationId).then(response => {
        this.setState({
          confirmed: response.data,
          confirmError: response.error,
          confirming: false
        }, () => {
          this.getUnconfirmed();
        });
      });
    });
  }

  onSearchChange = field => {
    let value = field.target.value.toLowerCase();
    this.setState({
      searchTerm: value
    }, () => this.filterList());
  }

  filterList = () => {
    let value = this.state.searchTerm;
    let filteredList = this.state.unconfirmedList.filter(
      u => u.firstname.toLowerCase().indexOf(value) > -1 || u.lastname.toLowerCase().indexOf(value) > -1 || u.email.toLowerCase().indexOf(value) > -1);
    this.setState({ filteredList: filteredList });
  }

  componentDidMount() {
    this.setState({ loading: true }, () => this.getUnconfirmed());
  }

  render() {
    const { loading,
      error,
      confirming,
      confirmError,
      confirmed,
      searchTerm,
      unconfirmedList,
      filteredList
    } = this.state;

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
        accessor: u =>
          <div className="registration-admin-fullname">
            {u.firstname + " " + u.lastname}
          </div>,
        minWidth: 150
      }, {
        id: "email",
        Header: <div className="registration-admin-email">Email</div>,
        accessor: u => u.email
      }, {
        id: "category",
        Header: <div className="registration-admin-category">Category</div>,
        accessor: u => u.user_category
      }, {
        id: "affiliation",
        Header: <div className="registration-admin-affiliation">Affiliation</div>,
        accessor: u => u.affiliation
      }, {
        id: "createdAt",
        Header: <div className="registration-admin-createdat">Registration Created At</div>,
        accessor: u => u.created_at
      }, {
        id: "confirm",
        Header: <div className="registration-admin-confirm">Confirm</div>,
        accessor: u => u.registration_id,
        Cell: props =>
          <button className="btn btn-success btn-sm"
            onClick={() => { this.onConfirm(props.value) }}
            disabled={confirming}>
            Confirm
          </button>,
      }
    ];

    return (
      <div className="RegistrationAdmin container-fluid pad-top-30-md">
        {error &&
          <div className={"alert alert-danger alert-container"}>
            {JSON.stringify(error)}
          </div>}

        <div class="card no-padding-h">
          <p className="h5 text-center mb-4 ">Unconfirmed Registrations</p>
          <div class="row mb-4">
            <div class="col-12">
              <FormTextBox placeholder="Search Full-name or Email"
                value={searchTerm}
                onChange={this.onSearchChange} />
            </div>
          </div>

          <div class="row">
            <div class="col-12">
              {unconfirmedList && unconfirmedList.length > 0 &&
                <ReactTable
                  data={filteredList}
                  columns={columns}
                  minRows={0} />
              }

              {confirmed && !confirmError &&
                <div class="alert alert-success alert-container">
                  {confirmed}
                </div>}

              {confirmError &&
                <div class="alert alert-danger alert-container">
                  {confirmError}
                </div>}

              {(!unconfirmedList || unconfirmedList.length === 0) &&
                <div class="alert alert-success alert-container">
                  There are no unconfirmed registrations
                </div>}
            </div>
          </div>
        </div>
      </div>
    )
  }
}

export default withRouter(RegistrationAdminComponent);