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
      selectedUserId: null
    };
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

  handleContinue = event => {
    this.setState({ showDetailsModal: false }, () => this.getAttendanceList());
  };

  handleUndo = event => {
    const { eventId, selectedUserId } = this.state;
    this.setState({ confirming: true }, () => {
      attendanceService
        .undoConfirmation(eventId, selectedUserId)
        .then(response => {
          this.setState(
            {
              confirmed: response.data,
              confirmError: response.error,
              confirming: false
            },
            () => {
              this.getAttendanceList();
              this.setState({
                showDetailsModal: false
              });
            }
          );
        });
    });
  };

  componentDidMount() {
    this.setState({ loading: true }, () => this.getAttendanceList());
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

  onConfirm = userId => {
    const { eventId } = this.state;
    this.setState({ selectedUserId: userId, confirming: true }, () => {
      attendanceService.confirm(eventId, userId).then(response => {
        this.setState(
          {
            confirmed: response.data,
            confirmError: response.error,
            confirming: false
          },
          () => {
            this.getAttendanceList();
            this.setState({
              showDetailsModal: true
            });
          }
        );
      });
    });
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
      },
      {
        id: "confirm",
        Header: (
          <div className="registration-admin-confirm">Mark attendance</div>
        ),
        accessor: u => u.registration_id,
        Cell: props => (
          <button
            className="btn btn-success btn-sm"
            onClick={e => {
              this.onConfirm(props.value);
            }}
            disabled={confirming}
          >
            Confirm
          </button>
        )
      }
    ];

    const {
      filteredList,
      loading,
      error,
      confirming,
      confirmError,
      confirmed,
      searchTerm,
      selectedUserId,
      originalAttendanceList
    } = this.state;
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
          <p>
            Are you SURE you want to withdraw your application to the Deep
            Learning Indaba 2019? You will NOT be considered for a place at the
            Indaba if you continue.
          </p>
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

              {confirmed && !confirmError && (
                <div class="alert alert-success">
                  Success for userId: {selectedUserId}
                </div>
              )}
              {confirmError && (
                <div class="alert alert-danger">{confirmError}</div>
              )}

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
