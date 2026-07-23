import React from "react";
import { withTranslation } from "react-i18next";
import ReactTable from "react-table";
import { attendanceService } from "../../../services/attendance/attendance.service";
import { checkinService } from "../../../services/eventApp/checkin.service";
import FormTextBox from "../../../components/form/FormTextBox";
import Modal, { ConfirmModal } from "../../../components/Modal";
import QrScanner from "../../../components/QrScanner";

function extractToken(decodedText) {
  try {
    const url = new URL(decodedText);
    const t = url.searchParams.get("t");
    if (t) return t;
  } catch (e) {}
  return decodedText;
}

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
      confirming: false,
      location: props.location,
      userAlreadyExists: null,
      showAllColumns: null,
      signedIndemnityChecked: false,
      linkUser: null,
      linkLoading: false,
      linkResult: null,
      showCheckedIn: false,
      undoTarget: null,
      undoLoading: false,
      undoBanner: null
    };
    this.linking = false;
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
        this.setState(
          {
            loading: false,
            originalAttendanceList: result.data,
            error: result.error
          },
          () => this.filterList()
        );
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

  openLink = user => {
    this.linking = false;
    this.setState({
      linkUser: { id: user.id, name: user.firstname + " " + user.lastname },
      linkResult: null,
      linkLoading: false
    });
  };

  closeLink = () => {
    this.linking = false;
    this.setState({ linkUser: null, linkResult: null, linkLoading: false });
  };

  handleLinkScan = decodedText => {
    const { eventId, linkUser } = this.state;
    if (this.linking || !linkUser) return;
    this.linking = true;
    const token = extractToken(decodedText);
    this.setState({ linkLoading: true });
    checkinService.linkBadge(eventId, linkUser.id, token).then(result => {
      this.linking = false;
      if (result.error) {
        this.setState({ linkLoading: false, linkResult: { type: "error", message: result.error } });
      } else {
        this.setState({ linkLoading: false, linkResult: { type: "success", message: this.props.t("Blank badge linked to {{name}}. Hand them this badge.", { name: linkUser.name }) } });
      }
    });
  };

  retryLink = () => {
    this.linking = false;
    this.setState({ linkResult: null, linkLoading: false });
  };

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

  openUndo = user => {
    this.setState({
      undoTarget: { id: user.id, name: user.firstname + " " + user.lastname },
      undoLoading: false,
      undoBanner: null
    });
  };

  closeUndo = () => {
    this.setState({ undoTarget: null, undoLoading: false });
  };

  confirmUndo = () => {
    const { eventId, undoTarget } = this.state;
    this.setState({ undoLoading: true }, () => {
      attendanceService.undoConfirmation(eventId, undoTarget.id).then(result => {
        const success = !result.error;
        this.setState(
          {
            undoTarget: null,
            undoLoading: false,
            undoBanner: {
              type: success ? "success" : "error",
              message: success
                ? this.props.t("Checked-in status undone for {{name}}", { name: undoTarget.name })
                : this.props.t("Failed to undo check-in for {{name}} due to {{error}}", { name: undoTarget.name, error: result.error })
            }
          },
          () => this.getAttendanceList()
        );
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
    const { searchTerm, showCheckedIn, originalAttendanceList } = this.state;
    const value = searchTerm || "";
    let filteredList = (originalAttendanceList || []).filter(
      u =>
        (u.firstname + " " + u.lastname).toLowerCase().indexOf(value) > -1 ||
        u.email.toLowerCase().indexOf(value) > -1
    );
    if (!showCheckedIn) {
      filteredList = filteredList.filter(u => !u.checked_in);
    }
    this.setState({ filteredList: filteredList });
  };

  onToggleShowCheckedIn = () => {
    this.setState(
      prevState => ({ showCheckedIn: !prevState.showCheckedIn }),
      () => this.filterList()
    );
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
    const { t } = this.props;
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
      confirmUser,
      showCheckedIn,
      undoTarget,
      undoLoading,
      undoBanner
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
        Header: <div className="text-left font-bold">{t("Full-Name")}</div>,
        accessor: u => <div className="font-medium text-foreground">{u.firstname + " " + u.lastname}</div>,
        minWidth: 150,
        sort: "asc"
      },
      {
        id: "email",
        Header: <div className="text-left font-bold">{t("Email")}</div>,
        accessor: u => u.email
      },
      {
        id: "confirm",
        Header: <div className="text-left font-bold">{t("Mark attendance")}</div>,
        accessor: u => u.user_id,
        minWidth: 300,
        Cell: props => (
          <div className="flex items-center gap-2 flex-wrap">
            {props.original.checked_in && (
              <>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-50 text-green-700 border border-green-200/50">{t("Checked In")}</span>
                <button
                  className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors border border-border text-foreground hover:bg-slate-50 cursor-pointer"
                  onClick={() => {
                    this.openUndo(props.original);
                  }}
                >
                  {t("Undo")}
                </button>
              </>
            )}
            {!props.original.checked_in && (
              <button
                className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50 cursor-pointer"
                onClick={() => {
                  this.onCheckin(props.original);
                }}
                disabled={confirming}
              >
                {t("Check-in")}
              </button>
            )}
            <button
              className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors border border-border text-foreground hover:bg-slate-50 cursor-pointer"
              onClick={() => {
                this.openLink(props.original);
              }}
            >
              {t("Link badge")}
            </button>
          </div>
        )
      }
    ];

    return (
      <div className="w-full pt-6 text-left space-y-6">
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
                  {t("UNPAID FEES - Please refer to special situations desk.")}
                </div>
              )}

              <div className="space-y-4">
                <div className="flex justify-between items-center text-sm py-2 border-b border-border/50">
                  <span className="text-muted-foreground font-semibold">{t("Role:")}</span>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/10 text-primary border border-primary/20">
                    {selectedUser.invitedguest_role}
                  </span>
                </div>

                <div className="flex justify-between items-center text-sm py-2 border-b border-border/50">
                  <span className="text-muted-foreground font-semibold">{t("Indemnity Form:")}</span>
                  {selectedUser.signed_indemnity_form ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-50 text-green-700 border border-green-200/50">{t("Signed")}</span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-error/10 text-error border border-error/20">{t("Not Signed.")}</span>
                  )}
                </div>

                {selectedUser.tags.length > 0 && (
                  <div className="flex justify-between items-start text-sm py-2 border-b border-border/50">
                    <span className="text-muted-foreground font-semibold mt-0.5">{t("Tags:")}</span>
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
                    {t("Have they signed a paper copy of the indemnity form?")}
                  </label>
                </div>
              )}

              <div className="flex justify-end gap-3 pt-4 border-t border-border/50">
                <button 
                  type="button" 
                  className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors border border-border text-muted-foreground hover:bg-slate-50 cursor-pointer bg-white"
                  onClick={this.handleContinue}>
                  {t("Cancel")}
                </button>
                <button
                  type="submit"
                  className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50 cursor-pointer"
                  disabled={!(selectedUser.signed_indemnity_form || signedIndemnityChecked) || !selectedUser.confirmed}
                  onClick={this.onConfirm}>
                  {t("Confirm")}
                </button>
              </div>
            </div>
          ) : <div></div>}
        </Modal>

        <Modal visible={!!this.state.linkUser}>
          {this.state.linkUser ? (
            <div className="p-6 space-y-4">
              <h3 className="text-lg font-bold text-foreground">
                {t("Link a blank badge to {{name}}", { name: this.state.linkUser.name })}
              </h3>

              {!this.state.linkResult && !this.state.linkLoading && (
                <>
                  <p className="text-sm text-muted-foreground">
                    {t("Scan the QR code on a blank badge to assign it to this attendee. Their ticket QR will switch to this badge.")}
                  </p>
                  <QrScanner onScan={this.handleLinkScan} />
                  <button
                    className="w-full px-4 py-2.5 rounded-lg border border-border text-sm font-medium text-foreground hover:bg-slate-50 cursor-pointer"
                    onClick={this.closeLink}
                  >
                    {t("Cancel")}
                  </button>
                </>
              )}

              {this.state.linkLoading && (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              )}

              {this.state.linkResult && (
                <div className="space-y-3">
                  <div className={
                    this.state.linkResult.type === "success"
                      ? "bg-green-50 text-green-700 border border-green-200 p-4 rounded-xl text-sm"
                      : "bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm"
                  }>
                    {this.state.linkResult.message}
                  </div>
                  {this.state.linkResult.type === "error" && (
                    <button
                      className="w-full px-4 py-2.5 rounded-lg border border-border text-sm font-medium text-foreground hover:bg-slate-50 cursor-pointer"
                      onClick={this.retryLink}
                    >
                      {t("Scan a different badge")}
                    </button>
                  )}
                  <button
                    className="w-full px-4 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 cursor-pointer"
                    onClick={this.closeLink}
                  >
                    {t("Done")}
                  </button>
                </div>
              )}
            </div>
          ) : <div></div>}
        </Modal>

        <ConfirmModal
          visible={!!undoTarget}
          onOK={this.confirmUndo}
          onCancel={this.closeUndo}
          okText={undoLoading ? t("Undoing...") : t("Yes, undo")}
          cancelText={t("Cancel")}
        >
          <p>
            {undoTarget &&
              t(
                "Are you sure you want to undo the check-in for {{name}}? This will remove their confirmed attendance and checked-in status.",
                { name: undoTarget.name }
              )}
          </p>
        </ConfirmModal>

        {undoBanner && (
          <div
            className={
              undoBanner.type === "success"
                ? "bg-green-50 text-green-700 border border-green-200 p-4 rounded-xl text-sm w-full text-center mt-6"
                : "bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6"
            }
          >
            {undoBanner.message}
          </div>
        )}

        {confirmStatus && (
          <div className="bg-green-50 text-green-700 border border-green-200 p-4 rounded-xl text-sm w-full text-center mt-6">
            {t("Successfully checked-in {{name}}", { name: confirmUser.fullname })}
          </div>
        )}

        {confirmStatus !== null && !confirmStatus && (
          <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
            {t("Failed to check-in {{name}} due to {{error}}", { name: confirmUser.fullname, error: confirmError })}
          </div>
        )}

        <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6" key="attendance-table">
          <h1 className="font-heading text-2xl font-bold text-foreground mb-6">{t("Check-in")}</h1>
          <div className="mb-4 space-y-3">
            <FormTextBox
              placeholder={t("Search Full-name or Email")}
              value={searchTerm}
              onChange={this.onSearchChange}
            />
            <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer select-none">
              <input
                type="checkbox"
                className="rounded border-border text-primary focus:ring-primary w-4 h-4 cursor-pointer"
                checked={showCheckedIn}
                onChange={this.onToggleShowCheckedIn}
              />
              {t("Show attendees who are already checked-in")}
            </label>
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
                {t("All attendances are confirmed.")}
              </div>
            )}

            {originalAttendanceList &&
              originalAttendanceList.length > 0 &&
              (!filteredList || filteredList.length === 0) && (
                <div className="bg-slate-50 text-muted-foreground border border-border p-4 rounded-xl text-sm w-full text-center">
                  {t("No attendees match your search.")}
                </div>
              )}
          </div>
        </div>
      </div>
    );
  }
}
export default withTranslation()(AttendanceTable);
