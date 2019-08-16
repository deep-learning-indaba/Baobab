import React, { Component } from "react";
import ReactTable from "react-table";
import { attendanceService } from "../../../services/attendance/attendance.service";
import FormTextBox from "../../../components/form/FormTextBox";
import { ConfirmModal } from "react-bootstrap4-modal";
class AttendanceTable extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      eventId: props.eventId,
      originalAttendanceList: [],
      filteredList: [],
      showDetailsModal: false,
      selectedUser: null,
      confirmResult: null,
      undoResult: null,
      confirming: false,
      undoing: false
    };
  }
  componentDidMount() {
    this.setState({ loading: true }, () => this.getAttendanceList());
  }
  getAttendanceList() {
    attendanceService.getAttendanceList(this.state.eventId).then(result => {
      this.setState({
        loading: false,
        originalAttendanceList: result.data,
        error: result.error,
        filteredList: result.data
      });
    });
  }
  onConfirm = user => {
    const { eventId } = this.state;
    this.setState({ selectedUser: user, confirming: true }, () => {
      attendanceService.confirm(eventId, user.user_id).then(result => {
        let success =
          (result.error == null || result.error == "") &&
          result.statusCode === 201;
        this.setState({
          showDetailsModal: success,
          confirming: false,
          confirmResult: {
            confirmed: result.data,
            confirmError: result.error,
            statusCode: result.statusCode,
            success: success
          }
        });
      });
    });
  };

  handleUndo = () => {
    const { eventId, selectedUser } = this.state;
    this.setState({ undoing: true }, () => {
      attendanceService
        .undoConfirmation(eventId, selectedUser.user_id)
        .then(response => {
          this.setState({
            undoResult: {
              undo: response.data,
              undoError: response.error,
              undoing: false
            }
          });
        });
    });
  };

  handleContinue = () => {
    this.setState(
      {
        showDetailsModal: false,
        loading: true,
        confirmResult: null,
        undoResult: null
      },
      () => this.getAttendanceList()
    );
  };

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
    const {
      filteredList,
      loading,
      error,
      confirming,
      undoing,
      confirmResult,
      undoResult,
      searchTerm,
      selectedUser,
      originalAttendanceList
    } = this.state;

    const loadingStyle = {
      width: "3rem",
      height: "3rem"
    };

    let confirmResultDiv = null;
    if (confirmResult) {
      if (confirmResult.success) {
        confirmResultDiv = (
          <div class="alert alert-success">
            Success - Attendance Confirmation.
          </div>
        );
      } else {
        confirmResultDiv = (
          <div class="alert alert-danger">
            {" "}
            Failure - Attendance Confirmation. Http Code:
            {confirmResult.statusCode} Message: {confirmResult.confirmError}
          </div>
        );
      }
    }

    let undoResultDiv = null;
    if (undoResult) {
      if (undoResult.undo && !undoResult.undoError) {
        undoResultDiv = (
          <div class="alert alert-success">
            Success - Undo Attendance Confirmation.
          </div>
        );
      } else {
        undoResultDiv = (
          <div class="alert alert-danger">
            {" "}
            Failure - Undo Attendance Confirmation. Message :{" "}
            {undoResult.undoError}
          </div>
        );
      }
    }

    let userInfoDiv = null;
    if (confirmResult && confirmResult.confirmed) {
      userInfoDiv = (
        <div>
          <h1>
            {selectedUser.firstname} {selectedUser.lastname}
          </h1>
          Category: {selectedUser.user_category} <br />
          Email: {selectedUser.email} <br />
          Event_id: {confirmResult.confirmed.event_id} <br />
          User_id: {confirmResult.confirmed.user_id} <br />
          Timestamp: {confirmResult.confirmed.timestamp} <br />
          Updated_by_user_id: {confirmResult.confirmed.updated_by_user_id}{" "}
          <br />
          Accommodation_award :{" "}
          {confirmResult.confirmed.accommodation_award !== null &&
            confirmResult.confirmed.accommodation_award.toString()}{" "}
          <br />
          Shirt_size :{" "}
          {confirmResult.confirmed.shirt_size !== null &&
            confirmResult.confirmed.shirt_size.toString()}{" "}
          <br />
          Is_Invitedguest :{" "}
          {confirmResult.confirmed.is_invitedguest !== null &&
            confirmResult.confirmed.is_invitedguest.toString()}{" "}
          <br />
        </div>
      );
    }
    const columns = [
      {
        id: "user",
        Header: <div>Full-Name</div>,
        accessor: u => <div>{u.firstname + " " + u.lastname}</div>,
        minWidth: 150,
        sort: "asc"
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
      },
      {
        id: "confirm",
        Header: (
          <div className="registration-admin-confirm">Mark attendance</div>
        ),
        accessor: u => u.user_id,
        Cell: props => (
          <button
            className="btn btn-success btn-sm"
            onClick={e => {
              this.onConfirm(props.original);
            }}
            disabled={confirming}
          >
            Confirm
          </button>
        )
      }
    ];

    if (loading) {
      return (
        <div class="d-flex justify-content-center">
          <div class="spinner-border" style={loadingStyle} role="status">
            <span class="sr-only">Loading...</span>
          </div>
        </div>
      );
    }

    return (
      <div className="container-fluid pad-top-30-md">
        {error && (
          <div className={"alert alert-danger"}>{JSON.stringify(error)}</div>
        )}
        <ConfirmModal
          visible={this.state.showDetailsModal}
          onOK={this.handleContinue}
          onCancel={this.handleUndo}
          okText={"Continue"}
          cancelText={"Undo"}
        >
          {userInfoDiv}
          {/* If we have an undo result - show it, otherwise show confirmed result. */}
          {undoResultDiv ||
            (confirmResult && confirmResult.success && confirmResultDiv)}
        </ConfirmModal>
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

              {confirmResult && !confirmResult.success && confirmResultDiv}

              {(!originalAttendanceList ||
                originalAttendanceList.length == 0) && (
                <div class="alert alert-success">
                  There are no unconfirmed attendances.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }
}
export default AttendanceTable;
