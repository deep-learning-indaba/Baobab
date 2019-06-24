import React, { Component } from "react";
import { withRouter } from "react-router";
import { profileService } from "../../../services/profilelist";
import { createColClassName } from "../../../utils/styling/styling";

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

const Row = ({RevieweName, ReviewerComments, ReviewerFinalVerdict}) => (
  <div className="row">
    <div>{RevieweName}</div>
    <div>{ReviewerComments}</div>
    <div>{ReviewerFinalVerdict}</div>
  </div>
);

class ViewProfileComponent extends Component {
  constructor(props) {
    super(props);
    this.state = {
      user: {},
      loading: true,
      error: "",
      isNull: true,
       applicationReviewList:{}
    };
  }

  displayReviewersTable =()=> {

    const rows = this.state.applicationReviewList.map( (rowData) => <Row {...rowData} />);

    return (
      <div className="table">
        <div className="header">
          <div>
            Reviewer Name</div>
          <div >
            Reviewer Comments</div>
          <div>
            Reviewer Final Verdict</div>
        </div>
        <div className="body">
          {rows}
        </div>
      </div>
    );
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
          Affiliation: result.affiliation,
          Department: result.department,
          Email: result.email,
          Firstname: result.firstname,
          is_Submitted: result.is_submitted,
          is_Withdrawn: result.is_withdrawn,
          Lastname: result.lastname,
          Response_id: result.response_id,
          Date_Submitted: date_submitted,
          Date_Withdrawn: date_withdrawn,
          User_Category: result.user_category,
          DateOfBirth: date,
          Gender: result.user_gender,
          ID: result.user_id,
          PrimaryLanguage: result.user_primaryLanguage,
          Title: result.user_title,

          Nationality: result.nationality_country,
          Residence: result.residence_country,
          Category: result.user_category_id,
          Disability: result.user_disability
        },
        loading: false,
        error: result.error,
        isNull: result.data === null
      });
    });

    profileService.getUserReview(DEFAULT_EVENT_ID, user_id).then(result => {
        this.setState({
          applicationReviewList:{
                review_by_user_firstname_list:result.review_by_user_firstname_list,
                Comments:result.Comments,
                Verdict:result.Verdict
              }
          });
    });
  }
  
  render() {
    const xs = 12;
    const sm = 6;
    const md = 6;
    const lg = 6;
    const commonColClassName = createColClassName(xs, sm, md, lg);
    const colClassNameTitle = createColClassName(12, 4, 2, 2);
    const colClassNameSurname = createColClassName(12, 4, 4, 4);
    const colClassEmailLanguageDob = createColClassName(12, 4, 4, 4);
    const {
      Affiliation,
      Department,
      Email,
      Firstname,
      is_Submitted,
      is_Withdrawn,
      Lastname,
      Response_id,
      Date_Submitted,
      Date_Withdrawn,
      User_Category,
      DateOfBirth,
      Gender,
      ID,
      PrimaryLanguage,
      Title,
      Nationality,
      Residence,
      Category,
      Disability
    } = this.state.user;
    const { loading, error, isNull } = this.state;
    const {review_by_user_firstname_list, Comments, Verdict} = this.state.applicationReviewList;
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
                Profile For : {Title + " " + Firstname + " " + Lastname}
              </div>
            </span>
            <form>
              <div class="row">
                <fieldset class="fieldset">
                  <legend class="legend">Personal Information </legend>
                  <div class="row">
                    <div class={colClassNameTitle}>
                      <div class="form-group">
                        <label
                          class="label-display col-form-label"
                          htmlFor="title"
                        >
                          Title:
                        </label>
                        <input
                          class="form-control"
                          type="text"
                          id="title"
                          value={Title}
                          readOnly
                        />
                      </div>
                    </div>
                    <div class={colClassNameSurname}>
                      <div class="form-group">
                        <label
                          class="label-display col-form-label"
                          htmlFor="firstname"
                        >
                          Firstname:
                        </label>
                        <input
                          class="form-control"
                          type="text"
                          id="firstname"
                          value={Firstname}
                          readOnly
                        />
                      </div>
                    </div>
                    <div class={colClassNameSurname}>
                      <div class="form-group">
                        <label
                          class="label-display col-form-label"
                          htmlFor="surname"
                        >
                          Surname:
                        </label>
                        <input
                          class="form-control"
                          type="text"
                          id="surname"
                          value={Lastname}
                          readOnly
                        />
                      </div>
                    </div>
                    <div class={colClassNameTitle}>
                      <div class="form-group">
                        <label
                          class="label-display col-form-label"
                          htmlFor="gender"
                        >
                          Gender:
                        </label>
                        <input
                          class="form-control"
                          type="text"
                          id="gender"
                          value={Gender}
                          readOnly
                        />
                      </div>
                    </div>
                  </div>
                  <div class="row">
                    <div class={colClassEmailLanguageDob}>
                      <div class="form-group">
                        <label
                          class="label-display col-form-label"
                          htmlFor="email"
                        >
                          Email Address:
                        </label>
                        <input
                          class="form-control"
                          type="text"
                          id="email"
                          value={Email}
                          readOnly
                        />
                      </div>
                    </div>
                    <div class={colClassEmailLanguageDob}>
                      <div class="form-group">
                        <label
                          class="label-display col-form-label"
                          htmlFor="dob"
                        >
                          Date Of Birth:
                        </label>
                        <input
                          class="form-control"
                          type="text"
                          id="dob"
                          value={DateOfBirth}
                          readOnly
                        />
                      </div>
                    </div>
                    <div class={colClassEmailLanguageDob}>
                      <div class="form-group">
                        <label
                          class="label-display col-form-label"
                          htmlFor="language"
                        >
                          Primary Language:
                        </label>
                        <input
                          class="form-control"
                          type="text"
                          id="language"
                          value={PrimaryLanguage}
                          readOnly
                        />
                      </div>
                    </div>
                  </div>

                  <div class="row">
                    <div class={colClassNameSurname}>
                      <div class="form-group">
                        <label
                          class="label-display col-form-label"
                          htmlFor="nationality"
                        >
                          Country of Nationality:
                        </label>
                        <input
                          class="form-control"
                          type="text"
                          id="nationality"
                          value={Nationality}
                          readOnly
                        />
                      </div>
                    </div>
                    <div class={colClassNameSurname}>
                      <div class="form-group">
                        <label
                          class="label-display col-form-label"
                          htmlFor="residence"
                        >
                          Country of Residence:
                        </label>
                        <input
                          class="form-control"
                          type="text"
                          id="residence"
                          value={Residence}
                          readOnly
                        />
                      </div>
                    </div>
                    <div class={colClassNameSurname}>
                      <div class="form-group">
                        <label
                          class="label-display col-form-label"
                          htmlFor="affiliation"
                        >
                          Affiliation:
                        </label>
                        <input
                          class="form-control"
                          type="text"
                          id="affiliation"
                          value={Affiliation}
                          readOnly
                        />
                      </div>
                    </div>
                  </div>
                  <div class="row">
                    <div class={colClassNameSurname}>
                      <div class="form-group">
                        <label
                          class="label-display col-form-label"
                          htmlFor="dept"
                        >
                          Department:
                        </label>
                        <input
                          class="form-control"
                          type="text"
                          id="dept"
                          value={Department}
                          readOnly
                        />
                      </div>
                    </div>
                    <div class={colClassNameSurname}>
                      <div class="form-group">
                        <label
                          class="label-display col-form-label"
                          htmlFor="category"
                        >
                          User Category:
                        </label>
                        <input
                          class="form-control"
                          type="text"
                          id="category"
                          value={User_Category}
                          readOnly
                        />
                      </div>
                    </div>
                    <div class={colClassNameSurname}>
                      <div class="form-group">
                        <label
                          class="label-display col-form-label"
                          htmlFor="disability"
                        >
                          Disability:
                        </label>
                        <input
                          class="form-control"
                          type="text"
                          id="disability"
                          value={Disability}
                          readOnly
                        />
                      </div>
                    </div>
                  </div>
                </fieldset>
              </div>
            
              <div class="row">
                <fieldset class="fieldset">
                  <legend class="legend">Application Comment Review </legend>
                    {this.displayReviewersTable}
                </fieldset>
              </div>

              <div class="row">
                <fieldset class="fieldset">
                  <legend class="legend">User Application Info. </legend>
                  <div class="row">
                    {is_Submitted && (
                      <div class={colClassNameSurname}>
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
                      <div class={colClassNameSurname}>
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
