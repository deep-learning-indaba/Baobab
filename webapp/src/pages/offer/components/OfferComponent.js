import React, { Component } from "react";
import { withRouter } from "react-router";
import { offerServices } from "../../../services/offer/offer.service";
import { applicationFormService } from "../../../services/applicationForm/applicationForm.service.js"
import { userService } from "../../../services/user/user.service";
import { NavLink } from "react-router-dom";
import { withTranslation } from 'react-i18next';

class Offer extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: {},
      userProfile: {},
      loading: true,
      error: "",
      rejected_reason: "",
      showReasonBox: false,
      candidate_response: null,
      offer: null,
      noOffer: null,
      category: "",
      awards: [],
      applicationExist: null
    };
  }

  resetPage = () => {
    this.componentWillMount()
  }

  handleChange = field => {
    return event => {
      this.setState({
        rejected_reason: event.target.value
      });
    };
  };

  buttonSubmit = (candidate_response) => {
    const { offer,
      rejected_reason,
      awards,
    } = this.state;

    const accepted_awards = awards.map(a => {
      return { 'id': a.id, 'accepted': a.accepted }}
      );

    if (candidate_response !== null) {
      offerServices
        .updateOffer(
          offer.id,
          this.props.event ? this.props.event.id : 0,
          candidate_response,
          candidate_response ? "" : rejected_reason,
          accepted_awards)
        .then(response => {
          if (response.response && response.response.status === 201) {
            this.setState({
              offer: response.response.data,
              awards: this.initAwards(response.response.data.tags),
              showReasonBox: false
            }, () => {
              this.displayOfferResponse();
              if (candidate_response && this.props.event) {
                this.props.history.push(`/${this.props.event.key}/registration`);
              }
            });
          } else if (response.error) {
            this.setState({
              error: response.error,
              showReasonBox: false
            });
          }
        });
    }
  }

  row = (col1, col2) => {
    return <div className="row mb-2">
      <div class="col-6 font-weight-bold pr-4" align="right">{col1}:</div>
      <div class="col-6 pl-4" align="left">{col2}</div>
    </div>
  }

  onChangeAward = award_id => {
    const u = this.state.awards;
    u.forEach(a => {
      if (a.id === award_id) {
        a.accepted = !a.accepted;
      }
    });
    this.setState({
      awards: u
    });
  }

  displayOfferResponse = () => {
    const { offer, awards } = this.state;
    const event = this.props.event;
    const t = this.props.t;
    let responded_date = offer.responded_at !== undefined ? offer.responded_at.substring(0, 10) : "-date-"

    return (
      <div className="container">
        <p className="h5 pt-5">
          {offer.candidate_response && <span>You accepted the following offer on {responded_date}.</span>}
          {!offer.candidate_response && <span class="text-danger">{t("You rejected your offer for a spot at") + " " + (event ? event.name : "") + " " + "on" + " " + responded_date + " " + t("for the following reason") + ":"}<br /><br />{offer.rejected_reason}</span>}
        </p>

        {offer.candidate_response && <div className="white-background card form mt-5">
          {this.row("Offer date", offer.offer_date !== undefined ? offer.offer_date.substring(0, 10) : "-date-")}
          {this.row("Offer expiry date", offer.expiry_date !== undefined ? offer.expiry_date.substring(0, 10) : "-date-")}
          {this.row("Registration fee", offer.payment_required ? (t("Payment of") + " " + offer.payment_amount + "USD" + " required to confirm your place"): t("Fee Waived"))}

          {this.props.event && awards && this.row(t("Awards"), t("You have accepted the following awards") + ": " + awards.filter(a => a.accepted).map(a => a.name).join(", "))}
        </div>}

        {offer.candidate_response &&
          <div className="row mt-4">
            <div className="col">
              <button
                type="button"
                class="btn btn-danger"
                id="reject"
                onClick={() => {
                  this.setState(
                    {
                      showReasonBox: true
                    });
                }}>
                Reject
                </button>
            </div>

            <div className="col">
              <NavLink className="btn btn-primary" to={`/${this.props.event.key}/registration`}>
                Proceed to Registration 
              </NavLink>
            </div>
          </div>
        }

        {this.state.showReasonBox &&
          <div className="row">
            <textarea
              class="form-control reason-box pr-5 pl-10 pb-5"
              onChange={this.handleChange(this.state.rejected_reason)}
              placeholder="Enter rejection message" />
            <button
              type="button"
              class="btn btn-outline-danger mt-2"
              align="center"
              onClick={() => {
                this.setState({
                  candidate_response: false
                },
                  this.buttonSubmit(false)
                );
              }}>
              Submit
            </button>
          </div>
        }
      </div>);
  }

  renderAwards = () => {
    const { awards } = this.state;
    const t = this.props.t;

    return <div class="row mb-3">
      <div class="col-md-3 font-weight-bold pr-2" align="left">{t("Awards")}</div>
      {awards ?
        <div>
        <div class="col-md-12 pr-2" align="left">{t("We are pleased to offer you the following awards") + ":"}</div>
          {awards.map((award) => {
            return <div class="row mb-3" align="center" key={"award_"+award.id}>
                      <div class="col-md-12" align="center">
                        <span class="font-weight-bold">{award.name + ": "}</span>
                        {award.description}
                      </div>
                      <div class="col-md-12" align="center">
                        <div class="form-check award-container">
                          <input type="checkbox" class="form-check-input"
                            checked={award.accepted}
                            onChange={() => this.onChangeAward(award.id)}
                            id={"check_" + award.id} />
                          <label class="form-check-label" htmlFor={"check_"+award.id}>{t("I accept this award")}.</label>
                        </div>
                      </div>
                    </div>
          })}
        </div>
        :
        <div class="row-mb-2 pr-2" align="center">{t("Unfortunately we are unable to grant you any awards for this event")}</div>
      } 
    </div>
  }

  displayOfferContent = e => {
    const { offer,
      rejected_reason,
      awards,
    } = this.state;

    const t = this.props.t;

    return (
      <div>
        {offer.candidate_response !== null ?
          this.displayOfferResponse()
          :
          <div className="container">
            <p className="h5 pt-5">
                {t("We are pleased to offer you a place at") + " " + (this.props.event ? this.props.event.name : "") + ". "}
                {t("Please see the details of this offer below") + "."}
            </p>

            <form class="form pt-2 ">

              <div className="white-background card form">
                <p class="font-weight-bold">{t("Offer Details")}</p>

                {this.props.event && awards && this.renderAwards()}

                <div class="row mb-3">
                  <div class="col-md-3 font-weight-bold pr-2" align="left">{t("Registration Fee")}</div>
                  <div class="col-md-6" align="left">

                    {offer && offer.payment_required && (t("In order to confirm your place, you will be liable for a") + " " + offer.payment_amount + "USD " + t("registration fee") + ".")}
                    {offer && !offer.payment_required && (t("Your registration fee has been waived") + ".")}
                  </div>
                </div>

                <p class="font-weight-bold">
                  {t("Please accept or reject this offer by")}{" "}
                  {offer !== null ? offer.expiry_date !== undefined ? offer.expiry_date.substring(0, 10) : "-date-" : "unable to load expiry date"}{" "}
                </p>

                <div class="form-group">
                  {this.state.showReasonBox ? (
                    <div class="form-group mr-5  ml-5 pt-5">
                      <textarea
                        class="form-control reason-box pr-5 pl-10 pb-5"
                        onChange={this.handleChange(rejected_reason)}
                        placeholder={t("Enter rejection message")} />
                      <button
                        type="button"
                        class="btn btn-outline-danger mt-2"
                        align="center"
                        onClick={() => {
                          this.setState(
                            {
                              candidate_response: false
                            },
                            this.buttonSubmit(false)
                          );
                        }}>
                        Submit
                  </button>
                    </div>
                  ) : (
                      <div class="row">
                        <div class="col" align="center">
                          <button
                            type="button"
                            class="btn btn-danger"
                            id="reject"
                            onClick={() => {
                              this.setState({
                                showReasonBox: true
                              });
                            }}>
                            Reject
                    </button>
                        </div>

                        <div class="col" align="center">
                          <button
                            type="button"
                            class="btn btn-success"
                            id="accept"
                            onClick={() => {
                              this.setState({
                                candidate_response: true
                              }
                              );
                              this.buttonSubmit(true)
                            }}>
                            Accept
                    </button>
                        </div>
                      </div>
                    )}

                </div>
              </div>
            </form>
          </div>
        }
      </div>
    );
  };

  componentWillMount() {
    userService.get().then(results => {
      this.setState({
        userProfile: results,
        error: results.error
      }, this.getOffer);
    });
  }

  componentDidMount() {
    applicationFormService.getResponse(this.props.event ? this.props.event.id : 0)
      .then(results => {
        if (results.response && results.response.length > 0 && results.response[0].is_submitted && !results.response[0].is_withdrawn) {
          this.setState({
            applicationExist: true
          });
        } else {
          this.setState({
            applicationExist: false
          });
        }
      });
  }

  getOffer = () => {
    this.setState({ loading: true });
    offerServices.getOffer(this.props.event ? this.props.event.id : 0)
      .then(result => {
        if (result.error && result.statusCode === 404) {
          this.setState({
            noOffer: true,
            loading: false
          });
        } else if (result.error) {
          this.setState({
            error: result.error,
            loading: false
          });
        } else {
          this.setState({
            loading: false,
            offer: result.offer,
            error: result.error,
            awards: this.initAwards(result.offer.tags)
          });
        }
      });
  }

  initAwards = (tags) => {
    return tags.filter(tag => tag.tag_type === "GRANT").map(tag => {
      return {
        ...tag,
        accepted: tag.accepted === null ? true : tag.accepted,
        }
      });
  }

  render() {

    const { loading, offer, error, applicationExist, noOffer } = this.state;
    const loadingStyle = {
      width: "3rem",
      height: "3rem"
    };
    const t = this.props.t;

    if (loading) {
      return (
        <div class="d-flex justify-content-center pt-5">
          <div className="spinner-border"
            style={loadingStyle}
            role="status">
            <span className="sr-only">Loading...</span>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div class="alert alert-danger" align="center">
          {error}
        </div>
      );
    }
    else if (offer !== null) {
      return this.displayOfferContent();
    }
    else if ((noOffer || offer === null) && !applicationExist) {
      return (
        <div className="h5 pt-5" align="center">
          {" "}
          You did not apply to attend.
        </div>
      );
    }
    else {
      return (
        <div className="h5 pt-5" align="center">
          {" "}
          {t("Please await further communication")}
        </div>
      );
    }
  }
}

export default withRouter(withTranslation()(Offer));
