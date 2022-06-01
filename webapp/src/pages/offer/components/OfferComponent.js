// TODO: ADD TRANSLATION

import React, { Component } from "react";
import { withRouter } from "react-router";
import { offerServices } from "../../../services/offer/offer.service";
import { applicationFormService } from "../../../services/applicationForm/applicationForm.service.js"
import { userService } from "../../../services/user/user.service";
import { NavLink } from "react-router-dom";


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
      accepted_accommodation_award: false,
      accepted_travel_award: false,
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
      accepted_accommodation_award,
      accepted_travel_award
    } = this.state;

    if (candidate_response !== null) {
      offerServices
        .updateOffer(
          offer.id,
          this.props.event ? this.props.event.id : 0,
          candidate_response,
          candidate_response ? "" : rejected_reason,
          accepted_accommodation_award,
          accepted_travel_award)
        .then(response => {
          if (response.response && response.response.status === 201) {
            this.setState({
              offer: response.response.data,
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

  onChangeAccommodation = () => {
    this.setState({
      accepted_accommodation_award: !this.state.accepted_accommodation_award
    });
  }

  onChangeTravel = () => {
    this.setState({
      accepted_travel_award: !this.state.accepted_travel_award
    });
  }

  displayOfferResponse = () => {
    const { offer } = this.state;
    const event = this.props.event;
    let responded_date = offer.responded_at !== undefined ? offer.responded_at.substring(0, 10) : "-date-"

    return (
      <div className="container">
        <p className="h5 pt-5">
          {offer.candidate_response && <span>You accepted the following offer on {responded_date}.</span>}
          {!offer.candidate_response && <span class="text-danger">You rejected your offer for a spot at {event ? event.name : ""} on {responded_date} for the following reason:<br /><br />{offer.rejected_reason}</span>}
        </p>

        {offer.candidate_response && <div className="white-background card form mt-5">
          {this.row("Offer date", offer.offer_date !== undefined ? offer.offer_date.substring(0, 10) : "-date-")}
          {this.row("Offer expiry date", offer.expiry_date !== undefined ? offer.expiry_date.substring(0, 10) : "-date-")}
          {this.row("Registration fee", offer.payment_required ? `Payment of ${offer.payment_amount} required to confirm your place` : "Fee Waived")}

          {this.props.event && this.props.event.travel_grant && this.row("Travel", offer.accepted_travel_award ? "Your travel to and from Tunis will be arranged by the Indaba" : "You are responsible for your own travel to and from Tunis.")}
          {this.props.event && this.props.event.travel_grant && this.row("Accommodation", offer.accepted_accommodation_award ? "Your accommodation will be covered by the Indaba in a shared hostel from the 21st to 26th August" : "You are responsible for your own accommodation in Tunis. We have secured hotel deals from 38 USD per night, details on how to book these will follow soon.")}
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

  renderTravelAward = (offer, accepted_travel_award) => {
    return <div class="row mb-4">
      <div class="col-md-3 font-weight-bold pr-2" align="center">Travel:</div>
      <div class="col-md-6" align="left">
        {offer && offer.travel_award && accepted_travel_award &&
          "We are pleased to offer you a travel award which will cover your flights to and from Tunis."}
        {offer && offer.travel_award && !accepted_travel_award &&
          <span class="text-danger">You have chosen to reject the travel award - you will be responsible for your own travel to and from Tunis!</span>}
        {offer && offer.requested_travel && !offer.travel_award &&
          "Unfortunately we are unable to grant you the travel award you requested in your application."}
        {offer && !offer.requested_travel && !offer.travel_award &&
          "You did not request a travel award. You will be responsible for your own travel to and from Tunis"}
      </div>

      <div class="col-md-3">
        {offer.travel_award &&
          <div class="form-check">
            <input type="checkbox" class="form-check-input" checked={accepted_travel_award} onChange={this.onChangeTravel}
              id="CheckTravel" />
            <label class="form-check-label" for="CheckTravel">I accept the travel award.</label>
          </div>}
      </div>
    </div>
  }

  renderAccommodationAward = (offer, accepted_accommodation_award) => {
    return <div class="row mb-2">
      <div class="col-md-3 font-weight-bold pr-2" align="center">Accommodation:</div>

      <div class="col-md-6" align="left">
        {offer && offer.accommodation_award && accepted_accommodation_award &&
          "We are pleased to offer you an accommodation award which will cover your stay between the 21st and 26th of August. Note that this will be in a shared hostel room (with someone of the same gender) at the university."}
        {offer && offer.accommodation_award && !accepted_accommodation_award &&
          <span class="text-danger">You have chosen to reject the accommodation award - you will be responsible for your own accommodation in Tunis during the Indaba! We have secured hotel deals from 38 USD per night, details on how to book these will follow soon.</span>}
        {offer && offer.requested_accommodation && !offer.accommodation_award &&
          <span>Unfortunately we are unable to grant you the accomodation award you requested in your application.
                    We have secured hotel deals from 38 USD per night, details on how to book these will follow soon.</span>}
        {offer && !offer.requested_accommodation && !offer.accommodation_award &&
          "You did not request an accommodation award. You will be responsible for your own accommodation during the Indaba. We have secured hotel deals from 38 USD per night, details on how to book these will follow soon."}
      </div>

      <div class="col-md-3">
        {offer.accommodation_award &&
          <div class="form-check accommodation-container">
            <input type="checkbox" class="form-check-input"
              checked={accepted_accommodation_award}
              onChange={this.onChangeAccommodation}
              id="CheckAccommodation" />
            <label class="form-check-label" for="CheckAccommodation">I accept the accommodation award.</label>
          </div>}
      </div>
    </div>
  }

  displayOfferContent = e => {
    const { offer,
      rejected_reason,
      accepted_accommodation_award,
      accepted_travel_award
    } = this.state;

    return (
      <div>
        {offer.candidate_response !== null ?
          this.displayOfferResponse()
          :
          <div className="container">
            <p className="h5 pt-5">
              We are pleased to offer you a place at {this.props.event ? this.props.event.name : ""}.
          Please see the details of this offer below{" "}
            </p>

            <form class="form pt-2 ">

              <div className="white-background card form">
                <p class="font-weight-bold">Offer Details</p>

                {this.props.event && this.props.event.travel_grant && this.renderTravelAward(offer, accepted_travel_award)}
                {this.props.event && this.props.event.travel_grant && this.renderAccommodationAward(offer, accepted_accommodation_award)}

                <div class="row mb-3">
                  <div class="col-md-3 font-weight-bold pr-2" align="center">Registration Fee:</div>
                  <div class="col-md-6" align="left">
                    {offer && offer.payment_required && `In order to confirm your place, you will be liable for a ${offer.payment_amount} registration fee.`}
                    {offer && !offer.payment_required && "Your registration fee has been waived."}
                  </div>
                </div>

                <p class="font-weight-bold">
                  Please accept or reject this offer by{" "}
                  {offer !== null ? offer.expiry_date !== undefined ? offer.expiry_date.substring(0, 10) : "-date-" : "unable to load expiry date"}{" "}
                </p>

                <div class="form-group">
                  {this.state.showReasonBox ? (
                    <div class="form-group mr-5  ml-5 pt-5">
                      <textarea
                        class="form-control reason-box pr-5 pl-10 pb-5"
                        onChange={this.handleChange(rejected_reason)}
                        placeholder="Enter rejection message" />
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
            accepted_accommodation_award: result.offer.accepted_accommodation_award === null ? result.offer.accommodation_award : result.offer.accepted_accommodation_award,
            accepted_travel_award: result.offer.accepted_travel_award === null ? result.offer.travel_award : result.offer.accepted_travel_award
          });
        }
      });
  }

  render() {

    const { loading, offer, error, applicationExist, noOffer } = this.state;
    const loadingStyle = {
      width: "3rem",
      height: "3rem"
    };

    if (loading) {
      return (
        <div class="d-flex justify-content-center pt-5">
          <div class="spinner-border"
            style={loadingStyle}
            role="status">
            <span class="sr-only">Loading...</span>
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
          Please await further communication
        </div>
      );
    }
  }
}

export default withRouter(Offer);
