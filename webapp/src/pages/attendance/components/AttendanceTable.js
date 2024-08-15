// TODO: ADD TRANSLATION

import React from "react";
import ReactTable from "react-table";
import { attendanceService } from "../../../services/attendance/attendance.service";
import FormTextBox from "../../../components/form/FormTextBox";
import Modal from "react-bootstrap4-modal";
import queryString from "query-string";
class AttendanceTable extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      eventId: props.eventId,
      originalAttendanceList: [],
      filteredList: [],
      showDetailsModal: false,
      selectedUser: null,
      confirmStatus: null,
      confirmError: null,
      undoResult: null,
      confirming: false,
      undoing: false,
      excludeCheckedIn: null,
      location: props.location,
      userAlreadyExists: null,
      showAllColumns: null,
      signedIndemnityChecked: false
    };
  }
  componentDidMount() {
    window.addEventListener("resize", this.resize);
    this.resize();
    let url = this.props.location;
    // Default only show people who haven't checked in.
    let excludeCheckedIn = true;
    if (url) {
      let params = queryString.parse(url);
      if (
        params &&
        params.excludeCheckedIn &&
        params.excludeCheckedIn.toLowerCase() === "false"
      ) {
        excludeCheckedIn = false;
      }
    }
    this.setState(
      { loading: true, excludeCheckedIn: excludeCheckedIn },
      () => this.getAttendanceList()
    );
  }

  resize = () => {
    this.setState({ showAllColumns: window.innerWidth >= 500 });
  };
  getAttendanceList() {
    const { excludeCheckedIn } = this.state;
    attendanceService
      .getAttendanceList(this.state.eventId, excludeCheckedIn)
      .then(result => {
        this.setState({
          loading: false,
          originalAttendanceList: result.data,
          error: result.error,
          filteredList: result.data
        });
      });
  }

  onCheckin = user => {
    console.log("On checkin, user is: ");
    console.log(user);
    const { eventId } = this.state;
    attendanceService.checkIn(eventId, user.id).then(result => {
      this.setState({
        selectedUser: result.data,
        showDetailsModal: true,
        confirming: true
      });
    })
  }

  onConfirm = () => {
    const { eventId, selectedUser, signedIndemnityChecked } = this.state;
    
    attendanceService.confirm(eventId, selectedUser.user_id, selectedUser.signed_indemnity_form || signedIndemnityChecked).then(result => {
      const success =
        (result.error === null || result.error === "") &&
        result.statusCode === 201;
      this.setState({
        showDetailsModal: false,
        confirming: false,
        selectedUser: null,
        confirmStatus: success, 
        confirmError: result.error
      }, ()=>this.getAttendanceList());
    });
  };
  getTrProps = (state, rowInfo) => {
    if (rowInfo) {
      return {
        style: {
          // background: rowInfo.original.confirmed === true ? "white" : "#dc3545",
          color: "black"
        }
      };
    }
    return {};
  };

  handleCancel = () => {
    this.setState({showDetailsModal: false, selectedUser: null});
  }

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
        loading: false,
        confirmStatus: null,
        confirmError: null,
        undoResult: null,
        signedIndemnityChecked: false,
        confirming: false
      });
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

  styleFromRole = (role) => {
    if (role === "General Attendee") {
      return "badge badge-dark";
    }
    if (role === "Speaker") {
      return "badge badge-success";
    }
    if (role === "Organiser") {
      return "badge badge-warning";
    }
    else {
      return "badge badge-primary";
    }
  }

  handleSignedIndemnityChanged = (e) => {
    if (e.target) {
        const value = e.target.checked | 0;
        this.setState({
            signedIndemnityChecked: value
        });
    }
  }
  
  render() {
    const {
      filteredList,
      loading,
      error,
      confirming,
      confirmStatus,
      confirmError,
      searchTerm,
      selectedUser,
      originalAttendanceList,
      signedIndemnityChecked
    } = this.state;

    const loadingStyle = {
      width: "3rem",
      height: "3rem"
    };

    if (loading) {
      return (
        <div class="d-flex justify-content-center">
          <div class="spinner-border" style={loadingStyle} role="status">
            <span class="sr-only">Loading...</span>
          </div>
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
        id: "confirm",
        Header: (
          <div className="registration-admin-confirm">Mark attendance</div>
        ),
        accessor: u => u.user_id,
        Cell: props => (
          <div>
              <button
                className="btn btn-success btn-sm"
                onClick={() => {
                  this.onCheckin(props.original);
                }}
                disabled={confirming}
              >
                Check-in
              </button>
          </div>
        )
      }
    ];

    return (
      <div className="container-fluid pad-top-30-md attendance">
        {error && (
          <div className={"alert alert-danger alert-container"}>
            {JSON.stringify(error)}
          </div>
        )}

        <Modal
          visible={this.state.showDetailsModal}>
          {selectedUser ? <div className="confirm-modal">
            <h3>
              {selectedUser.fullname}
            </h3>
            {/* // TODO: Check */}
            {!selectedUser.confirmed && <div className="alert alert-danger">
              !Payment Required! Please refer to special situations desk.  
              </div>}
            <h5>
              Role:
              <div className={this.styleFromRole(selectedUser.invitedguest_role)}>
                {selectedUser.invitedguest_role}
              </div>
            </h5>              
            {selectedUser.registration_metadata.map((i) => (  // TODO: Replace with tags! 
              <h5>
                {i.name} :
                <div className="badge badge-light">
                  {i.response}
                </div>
              </h5>
            ))}
            <h5>
              Indemnity Form :
              {selectedUser.signed_indemnity_form && <div className="badge badge-success">
                Signed
              </div>}
              {!selectedUser.signed_indemnity_form && <div className="badge badge-danger">
                Not Signed.
              </div>}
            </h5>
            {!selectedUser.signed_indemnity_form && <div>
              <label>
                <input type="checkbox" 
                  className="confirm-idemnity"
                  checked={signedIndemnityChecked}
                  onChange={this.handleSignedIndemnityChanged}/>
                <span className="confirm-identity-label">Have they signed a paper copy of the indemnity form?</span>
              </label>
            </div>}
            <button 
              type="submit" 
              className="btn btn-primary confirm-submit"
              disabled={!(selectedUser.signed_indemnity_form || signedIndemnityChecked) || !selectedUser.confirmed} 
              onClick={this.onConfirm}>
                Confirm
            </button>
            <button 
              type="cancel" 
              className="btn btn-secondary confirm-cancel"
              onClick={this.handleContinue}>
                Cancel
            </button>
          </div> : <div></div>}
        </Modal>
        

        {confirmStatus && <div class="alert alert-success alert-container">
          Successfully checked-in.
        </div>}
        
        {confirmStatus !== null && !confirmStatus && <div class="alert alert-danger alert-container">
          Failed to check-in due to {confirmError}
        </div>}
            
        <div class="card no-padding-h">
          <p className="h5 text-center mb-4 ">Check-in</p>
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
                <ReactTable
                  data={filteredList}
                  columns={columns}
                  minRows={0}
                  getTrProps={this.getTrProps}
                />
              )}

              {(!originalAttendanceList ||
                originalAttendanceList.length === 0) && (
                  <div class="alert alert-success alert-container">
                    All attendances are confirmed.
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
