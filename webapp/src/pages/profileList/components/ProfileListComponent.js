import React, { Component } from "react";
import { withRouter } from "react-router";
import ReactTable from "react-table";
import { profileService } from "../../../services/profilelist";
import { withTranslation } from "react-i18next";

class ProfileListComponent extends Component {
  constructor(props) {
    super(props);
    this.state = {
      List: [],
      isEmpty: true,
      loading: true,
      error: "",
      Desc_Asc: true,
    };
  }

  isListEmpty(list) {
    return list.length === 0;
  }

  onChangeSorting = () => {
    this.setState({ Desc_Asc: !this.state.Desc_Asc });
  };
  componentDidMount() {
    profileService
      .getProfilesList(this.props.event ? this.props.event.id : 0)
      .then((results) => {
        this.setState({
          List: results.List,
          isEmpty: this.isListEmpty(results.List),
          loading: false,
          error: results.error,
        });
      });
  }

  onSubmit = (user_id) => {
    const { eventKey } = this.props.match.params;
    window.location = eventKey + "/viewprofile/:" + user_id;
  };

  render() {
    const { List, isEmpty, loading, error } = this.state;

    const loadingStyle = {
      width: "3rem",
      height: "3rem",
    };

    const t = this.props.t;

    const columns = [
      {
        id: "user",
        Header: <div className="list-fullname">{t("Full Name")}</div>,
        accessor: (u) => u.lastname + " " + u.firstname + ", " + u.user_title,
        Cell: (props) => (
          <button
            className="link-style"
            onClick={(e) => {
              e.preventDefault();
              this.onSubmit(props.original.user_id);
            }}
          >
            {props.value}
          </button>
        ),
        minWidth: 150,
      },

      {
        Header: <div className="list-type">{t("Type")}</div>,
        accessor: "type",
      },
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

    if (error) {
      return <div class="alert alert-danger alert-container">{error}</div>;
    }

    return (
      <div>
        {isEmpty ? (
          <div className="error-message-empty-list">
            <div className="alert alert-danger alert-container">
              {t("There are currently no user profiles to display!")}
            </div>
          </div>
        ) : (
          <div className="review-padding">
            {" "}
            <span className="review-padding">
              <div className="alert alert-primary table-header">
                {t("Total Profiles")}: {List.length}
              </div>
            </span>
            <ReactTable
              data={List}
              columns={columns}
              minRows={0}
              multiSort={true}
            />
          </div>
        )}
      </div>
    );
  }
}

export default withRouter(withTranslation()(ProfileListComponent));
