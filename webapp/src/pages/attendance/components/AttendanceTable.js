// TODO: ADD TRANSLATION

import React from "react";
import ReactTable from "react-table";
import { attendanceService } from "../../../services/attendance/attendance.service";
import FormTextBox from "../../../components/form/FormTextBox";
import Modal from "../../../components/Modal";

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
      confirmUser: null,
      confirmError: null,
      undoResult: null,
      confirming: false,
      undoing: false,
      location: props.location,
      userAlreadyExists: null,
      showAllColumns: null,
      signedIndemnityChecked: false
    };
  }
  componentDidMount() {
    window.addEventListener("resize", this.resize);
    this.resize();
    
    this.setState(
      { loading: true },
      () => this.getAttendanceList()
    );
  }

  resize = () => {
    this.setState({ showAllColumns: window.innerWidth >= 500 });
  };
  getAttendanceList() {
    attendanceService
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

  onCheckin = user => {
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
        confirmUser: selectedUser,
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
        (u.firstname + " " + u.lastname).toLowerCase().indexOf(value) > -1 ||
        u.email.toLowerCase().indexOf(value) > -1
    );
    this.setState({ filteredList: filteredList });
  };

  styleFromRole = (role) => {
    if (role === "Volunteer") {
      return "badge badge-primary";
    }
    if (role === "Organiser") {
      return "badge badge-danger";
    }
    if (["Sponsor", "Dignitary"].includes(role)) {
      return "badge badge-yellow";
    }
    if (["Speaker", "Workshop Organiser", "Workshop Speaker", "Mentor"].includes(role)) {
      return "badge badge-black";
    }
    if (role === "Press") {
      return "badge badge-purple";
    }
    else {
      return "badge badge-success";
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
      signedIndemnityChecked,
      confirmUser
    } = this.state;

    if (loading) {
      return (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      );
    }

    const columns = [
      {
        id: "user",
        Header: <div className="text-left font-bold">Full-Name</div>,
        accessor: u => <div className="font-medium text-foreground">{u.firstname + " " + u.lastname}</div>,
        minWidth: 150,
        sort: "asc"
      },
      {
        id: "email",
        Header: <div className="text-left font-bold">Email</div>,
        accessor: u => u.email
      },
      {
        id: "confirm",
        Header: <div className="text-left font-bold">Mark attendance</div>,
        accessor: u => u.user_id,
        Cell: props => (
          <div>
            {props.original.checked_in && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-50 text-green-700 border border-green-200/50">Checked In</span>
            )}
            {!props.original.checked_in && (
              <button
                className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50 cursor-pointer"
                onClick={() => {
                  this.onCheckin(props.original);
                }}
                disabled={confirming}
              >
                Check-in
              </button>
            )}
          </div>
        )
      }
    ];

    return (
      <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-6">
        {error && (
          <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
            {JSON.stringify(error)}
          </div>
        )}

        <Modal
          visible={this.state.showDetailsModal}>
          {selectedUser ? (
            <div className="confirm-modal p-6 space-y-6">
              <h3 className="text-lg font-bold text-foreground">
                {selectedUser.fullname}
              </h3>

              {!selectedUser.confirmed && (
                <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm font-semibold">
                  UNPAID FEES - Please refer to special situations desk.  
                </div>
              )}
              
              <div className="space-y-4">
                <div className="flex justify-between items-center text-sm py-2 border-b border-border/50">
                  <span className="text-muted-foreground font-semibold">Role:</span>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
                    {selectedUser.invitedguest_role}
                  </span>
                </div>

                <div className="flex justify-between items-center text-sm py-2 border-b border-border/50">
                  <span className="text-muted-foreground font-semibold">Indemnity Form:</span>
                  {selectedUser.signed_indemnity_form ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-50 text-green-700 border border-green-200/50">Signed</span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-error/10 text-error border border-error/20">Not Signed.</span>
                  )}
                </div>

                {selectedUser.tags.length > 0 && (
                  <div className="flex justify-between items-start text-sm py-2 border-b border-border/50">
                    <span className="text-muted-foreground font-semibold mt-0.5">Tags:</span>
                    <div className="flex flex-wrap gap-1 justify-end max-w-[70%]">
                      {selectedUser.tags.map((i) => (
                        <span key={i} className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-muted-foreground border border-border">{i}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {!selectedUser.signed_indemnity_form && (
                <div className="flex items-start gap-2 pt-2">
                  <input type="checkbox" 
                    id="confirm-indemnity-chk"
                    className="rounded border-border text-primary focus:ring-primary w-4 h-4 cursor-pointer mt-0.5"
                    checked={signedIndemnityChecked}
                    onChange={this.handleSignedIndemnityChanged}/>
                  <label htmlFor="confirm-indemnity-chk" className="text-sm text-muted-foreground cursor-pointer select-none">
                    Have they signed a paper copy of the indemnity form?
                  </label>
                </div>
              )}

              <div className="flex justify-end gap-3 pt-4 border-t border-border/50">
                <button 
                  type="button" 
                  className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors border border-border text-muted-foreground hover:bg-slate-50 cursor-pointer bg-white"
                  onClick={this.handleContinue}>
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50 cursor-pointer"
                  disabled={!(selectedUser.signed_indemnity_form || signedIndemnityChecked) || !selectedUser.confirmed} 
                  onClick={this.onConfirm}>
                  Confirm
                </button>
              </div>
            </div>
          ) : <div></div>}
        </Modal>
        

        {confirmStatus && (
          <div className="bg-green-50 text-green-700 border border-green-200 p-4 rounded-xl text-sm w-full text-center mt-6">
            Successfully checked-in {confirmUser.fullname}
          </div>
        )}
        
        {confirmStatus !== null && !confirmStatus && (
          <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
            Failed to check-in {confirmUser.fullname} due to {confirmError}
          </div>
        )}
            
        <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6" key="attendance-table">
          <h1 className="font-heading text-2xl font-bold text-foreground mb-6">Check-in</h1>
          <div className="mb-4">
            <FormTextBox
              placeholder="Search Full-name or Email"
              value={searchTerm}
              onChange={this.onSearchChange}
            />
          </div>
          <div className="react-table">
            {filteredList && filteredList.length > 0 && (
              <ReactTable
                data={filteredList}
                columns={columns}
                minRows={0}
                getTrProps={this.getTrProps}
                className="ReactTable"
              />
            )}

            {(!originalAttendanceList || originalAttendanceList.length === 0) && (
              <div className="bg-green-50 text-green-800 border border-green-200 p-4 rounded-xl text-sm w-full text-center">
                All attendances are confirmed.
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }
}
export default AttendanceTable;
