import React, { Component } from "react";
import { withRouter } from "react-router";
import { profileService } from "../../../services/profilelist";
import { createColClassName } from "../../../utils/styling/styling";
import validationFields from "../../../utils/validation/validationFields";
import FormTextBox from "../../../components/form/FormTextBox";

// const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

class ViewProfileComponent extends Component {
  constructor(props) {
    super(props);
    this.state = {
      user: {},
      loading: true,
      error: "",
      isNull: true
    };
  }

  componentDidMount() {
    const { id } = this.props.match.params;
    let user_id = parseInt(id.toString().split(":")[1], 10);
    profileService.getUserProfile(user_id).then(result => {
      var date = result.user_dateOfBirth;
      if (date) date = date.split("T")[0];
      var date_submitted = result.submitted_timestamp;
      if (date_submitted) date_submitted = date_submitted.split("T")[0];
      var date_withdrawn = result.withdrawn_timestamp;
      if (date_withdrawn) date_withdrawn = date_withdrawn.split("T")[0];
      this.setState({
        user: {
          email: result.email,
          title: result.user_title,
          firstName: result.firstname,
          lastName: result.lastname,
          is_Submitted: result.is_submitted,
          is_Withdrawn: result.is_withdrawn,
          Response_id: result.response_id,
          Date_Submitted: date_submitted,
          Date_Withdrawn: date_withdrawn,
          ID: result.user_id,
        },
        loading: false,
        error: result.error,
        isNull: result.data === null
      });
    });
  }
  render() {

    const commonColClassName = createColClassName(12, 4, 4, 4);
    const colClassNameUserApplicationInfo = createColClassName(12, 4, 4, 4);
    const {
      email,
      title,
      firstName,
      lastName,
      is_Submitted,
      is_Withdrawn,
      Date_Submitted,
      Date_Withdrawn,
    } = this.state.user;
    const { loading, error, isNull } = this.state;
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
    if (error) {
      return <div class="alert alert-danger">{error}</div>;
    }
    return (
      <div className="user-profile-container justify-content-center">
        {isNull ? (
          <div className="error-message-empty-list">
            <div className="alert alert-danger">
              No user profile to display!
            </div>
          </div>
        ) : (
            <div className="profile-view-padding">
              {" "}
              <span className="profile-view-padding">
                <div className="alert alert-primary user-profile-header">
                  Profile For : {title + " " + firstName + " " + lastName}
                </div>
              </span>
              <form>
                <div class="row">
                  <fieldset class="fieldset">
                    <legend class="legend">Personal Information </legend>
                    <div class="row">
                      <div class={commonColClassName}>
                        <FormTextBox
                          id={validationFields.title.name}
                          placeholder={validationFields.title.display}
                          value={title}
                          label={validationFields.title.display}
                        />
                      </div>
                      <div class={commonColClassName}>
                        <FormTextBox
                          id={validationFields.firstName.name}
                          type="text"
                          placeholder={validationFields.firstName.display}
                          value={firstName}
                          label={validationFields.firstName.display}
                        />
                      </div>
                      <div class={commonColClassName}>
                        <FormTextBox
                          id={validationFields.lastName.name}
                          type="text"
                          placeholder={validationFields.lastName.display}
                          value={lastName}
                          label={validationFields.lastName.display}
                          editable={false}
                        />
                      </div>
                    </div>
                    <div class="row">
                      <div class={commonColClassName}>
                        <FormTextBox
                          id={validationFields.email.name}
                          type="email"
                          placeholder={validationFields.email.display}
                          value={email}
                          label={validationFields.email.display}
                        />
                      </div>
                    </div>

                  </fieldset>
                </div>

                <div class="row">
                  <fieldset class="fieldset">
                    <legend class="legend">User Application Info. </legend>
                    <div class="row" class={colClassNameUserApplicationInfo}>
                      {is_Submitted && (
                        <div >
                          <div class="form-group">
                            <div
                              class="alert alert-success yes-submitted-alert"
                              role="alert"
                            >
                              Submitted on {Date_Submitted}
                            </div>
                          </div>
                        </div>
                      )}
                      {is_Withdrawn && (
                        <div class={colClassNameUserApplicationInfo}>
                          <div class="form-group">
                            <div
                              class="alert alert-danger no-submitted-alert"
                              role="alert"
                            >
                              Withdrawn on {Date_Withdrawn}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </fieldset>
                </div>
              </form>
            </div>
          )}
      </div>
    );
  }
}

export default withRouter(ViewProfileComponent);
