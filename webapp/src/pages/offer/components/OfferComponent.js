import React, { Component } from "react";
import { withRouter } from "react-router";
import { offerServices } from "../../../services/offer/offer.service";
import { applicationFormService } from "../../../services/applicationForm/applicationForm.service.js"
import { userService } from "../../../services/user/user.service";
import { NavLink } from "react-router-dom";
import { Trans, withTranslation } from 'react-i18next';
import { getDownloadURL } from "../../utils/files";

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
      grant_tags: [],
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
      grant_tags,
    } = this.state;

    if (candidate_response !== null) {
      offerServices
        .updateOffer(
          offer.id,
          this.props.event ? this.props.event.id : 0,
          candidate_response,
          candidate_response ? "" : rejected_reason,
          grant_tags.map(t => {
            return { 'id': t.id, 'accepted': t.accepted }}
            ))
        .then(response => {
          if (response.response && response.response.status === 201) {
            this.setState({
              offer: response.response.data,
              grant_tags: this.initGrants(response.response.data.tags),
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

  onChangeGrant = tag_id => {
    const u = this.state.grant_tags;
    u.forEach(t => {
      if (t.id === tag_id) {
        t.accepted = !t.accepted;
      }
    });
    this.setState({
      grant_tags: u
    });
  }

  displayOfferResponse = () => {
    const { offer, grant_tags } = this.state;
    const event = this.props.event;
    const t = this.props.t;

    const eventName = event ? event.name : "";
    const respondedDate = offer.responded_at ? offer.responded_at.substring(0, 10) : "-date-";
    const paymentAmount = offer.payment_amount;
    const paymentCurrency = offer.payment_currency;
    const acceptedGrants = grant_tags.filter(a => a.accepted);

    return (
      <div className="container">
        <p className="h5">
          {offer.candidate_response && offer.is_paid && <span><Trans i18nKey="spotAccepted">You accepted the following offer on {respondedDate}</Trans>.</span>}
          {!offer.candidate_response && <span><Trans i18nKey="spotRejected">You rejected your offer for a spot at {{eventName}} on {{respondedDate}} for the following reason:</Trans><br/><br/>{offer.rejected_reason}</span>}
          {offer.candidate_response && !offer.is_paid && !offer.is_expired && <span>{t("Your offer is pending receipt of payment")}</span>}
          {offer.candidate_response && !offer.is_paid && offer.is_expired && <span className="alert alert-danger">{t("Your offer has expired due to non payment")}</span>}
        </p>

        {offer.candidate_response && (offer.is_paid || (!offer.is_paid && !offer.is_expired)) && <div className="white-background card form mt-5 offer-container">
          {this.row("Offer date", offer.offer_date ? offer.offer_date.substring(0, 10) : "-date-")}
          {this.row("Offer expiry date", offer.expiry_date ? offer.expiry_date.substring(0, 10) : "-date-")}
          {this.row("Registration fee", offer.payment_required ? <Trans i18nKey="paymentRequired">Payment of {{paymentAmount}} {{paymentCurrency}} is required to confirm your place</Trans>: t("Fee Waived"))}

          {this.props.event && acceptedGrants.length > 0 && this.row(t("Grants"), t("You have accepted the following grants") + ": " + acceptedGrants.map(a => a.name).join(", "))}
        </div>}

        {offer.candidate_response && offer.is_paid &&
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
                {t("Reject")}
                </button>
            </div>

            <div className="col">
              <NavLink className="btn btn-primary" to={`/${this.props.event.key}/registration`}>
                {t("Proceed to Registration")}
              </NavLink>
            </div>
          </div>
        }

        {
          // If the user has accepted the offer but has not paid the registration fee, and the offer is not expired, show the invoice & payment button
          offer.candidate_response && !offer.is_paid && !offer.is_expired &&
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
                {t("Reject")}
              </button>
            </div>

            <div className="col">
              <a href={getDownloadURL(this.props.value, "indaba-invoices")}>
                {t("View Invoice")}
              </a>
            </div>
            <div className="col">
              <NavLink className="btn btn-primary" to={`/payment/${offer.invoice_id}`}>
                {t("Pay Online")}
              </NavLink>
            </div>
          </div>
        }

        {this.state.showReasonBox &&
          <div className="row">
            <textarea
              class="form-control reason-box pr-5 pl-10 pb-5"
              onChange={this.handleChange(this.state.rejected_reason)}
              placeholder={t("Please let us know why you are rejecting this offer")} />
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
              {t("Submit")}
            </button>
          </div>
        }
      </div>);
  }

  renderGrants = () => {
    const { grant_tags } = this.state;
    const t = this.props.t;

    return <div class="row mb-3">
      <div class="col-md-3 font-weight-bold pr-2 h4" align="left">{t("Grants")}</div>
      {grant_tags.length > 0 ?
        <div>
          <div class="col-md-12 pr-2" align="left">
            <div className="mb-5">{t("We are pleased to offer you the following grants") + ":"}</div>
          </div>
          {grant_tags.map((grant_tag) => {
            return <div class="row mb-3" align="left" key={"grant_tag_"+grant_tag.id}>
                      <div class="col-md-2">
                        <span class="font-weight-bold">{grant_tag.name}</span>
                        
                      </div>
                      <div class="col-md-8">
                        {grant_tag.description}
                      </div>
                      <div class="col-md-2">
                        <div class="form-check grant-container">
                          <input type="checkbox" class="form-check-input"
                            checked={grant_tag.accepted}
                            onChange={() => this.onChangeGrant(grant_tag.id)}
                            id={"check_" + grant_tag.id} />
                          <label class="form-check-label" htmlFor={"check_"+grant_tag.id}>{t("I accept this grant")}.</label>
                        </div>
                      </div>
                    </div>
          })}
        </div>
        :
        <div class="row-mb-2 pr-2" align="center">{t("Unfortunately we are unable to award you any grants for this event")}</div>
      } 
      <hr/>
    </div>
  }

  displayOfferContent = e => {
    const { offer,
      rejected_reason,
      grant_tags,
    } = this.state;

    const t = this.props.t;
    const paymentAmount = offer.payment_amount;
    const paymentCurrency = offer.payment_currency;

    return (
      <div>
        {offer.candidate_response !== null ?
          this.displayOfferResponse()
          :
          <div className="container">
            <p className="h5">
                {t("We are pleased to offer you a place at") + " " + (this.props.event ? this.props.event.name : "") + ". "}
                {t("Please see the details of this offer below") + "."}
            </p>

            <form class="form offer-container">

              <div className="white-background card form">
                <p class="font-weight-bold h3">{t("Offer Details")}</p>

                {this.props.event && grant_tags && this.renderGrants()}

                <div class="row">
                  <div class="col-md-12 font-weight-bold pr-2 h4" align="left">{t("Registration Fee")}</div>
                </div>
                <div class="row mb-5">
                  <div class="col-md-12" align="left">
                    {offer && offer.payment_required && <Trans i18nKey="registrationFee">In order to confirm your place, you will be liable for a {{paymentAmount}} {{paymentCurrency}} registration fee.</Trans>}
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
                        {t("Submit")}
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
                            {t("Reject")}
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
                            {t("Accept")}
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
            grant_tags: this.initGrants(result.offer.tags)
          });
        }
      });
  }

  initGrants = (tags) => {
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
          {t("You did not apply to attend")}.
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
