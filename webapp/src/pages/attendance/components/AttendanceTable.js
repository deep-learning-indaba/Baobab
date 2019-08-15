import React, { Component } from "react";
import ReactTable from "react-table";
import { registrationAdminService } from "../../../services/registration/registration.admin.service";
import FormTextBox from "../../../components/form/FormTextBox";
class AttendanceTable extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      eventId: props.eventId,
      originalAttendanceList: [],
      filteredList: []
    };
  }
  getRegistrationList() {
    registrationAdminService
      .getAttendanceList(this.state.eventId)
      .then(result => {
        this.setState({
          loading: false,
          originalAttendanceList: result.data,
          error: result.error,
          filteredList: result.data
        });
      });
  }

  componentDidMount() {
    this.setState({ loading: true }, () => this.getRegistrationList());
  }

  onSearchChange = field => {
    let value = field.target.value.toLowerCase();
    this.setState(
      {
        searchTerm: value
      },
      () => this.filterList()
    );
  };

  filterList = () => {
    let value = this.state.searchTerm;
    let filteredList = this.state.originalAttendanceList.filter(
      u =>
        u.firstname.toLowerCase().indexOf(value) > -1 ||
        u.lastname.toLowerCase().indexOf(value) > -1 ||
        u.email.toLowerCase().indexOf(value) > -1
    );
    this.setState({ filteredList: filteredList });
  };
  render() {
    const columns = [
      {
        id: "user",
        Header: <div>Full-Name</div>,
        accessor: u => <div>{u.firstname + " " + u.lastname}</div>,
        minWidth: 150
      },
      {
        id: "email",
        Header: <div>Email</div>,
        accessor: u => u.email
      },
      {
        id: "affiliation",
        Header: <div>Affiliation</div>,
        accessor: u => u.affiliation
      },
      {
        id: "role",
        Header: <div>Category</div>,
        accessor: u => u.user_category
      }
    ];

    const {
      filteredList,
      loading,
      error,
      confirming,
      confirmError,
      confirmed,
      searchTerm
    } = this.state;
    return (
      <div className="container-fluid pad-top-30-md">
        {error && (
          <div className={"alert alert-danger"}>{JSON.stringify(error)}</div>
        )}

        <div class="card no-padding-h">
          <p className="h5 text-center mb-4 ">Attendance Registration</p>
          <div class="row mb-4">
            <div class="col-12">
              <FormTextBox
                placeholder="Search Full-name or Email"
                value={searchTerm}
                onChange={this.onSearchChange}
              />
            </div>
          </div>
          <div class="row">
            <div class="col-12">
              {filteredList && filteredList.length > 0 && (
                <ReactTable data={filteredList} columns={columns} minRows={0} />
              )}

              {confirmed && !confirmError && (
                <div class="alert alert-success">{confirmed}</div>
              )}
              {confirmError && (
                <div class="alert alert-danger">{confirmError}</div>
              )}
              {/* 
              {(!unconfirmedList || unconfirmedList.length == 0) && (
                <div class="alert alert-success">
                  There are no unconfirmed registrations
                </div>
              )} */}
            </div>
          </div>
        </div>
      </div>
    );
  }
}
export default AttendanceTable;
