import React, { Component } from "react";
import { withRouter } from "react-router";
import { offerServices } from "../../../services/offer/offer.service";
import { profileService } from "../../../services/profilelist/profilelist.service";

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

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
      offer: {},
      category: ""
    };
  }

  handleChange = field => {
    return event => {
      this.setState({
        rejected_reason: event.target.value
      });
    };
  };

  buttonSubmit(candidate_response) {
    const { offer, rejected_reason } = this.state;

    offerServices
      .updateOffer(
        offer.id,
        DEFAULT_EVENT_ID,
        candidate_response,
        candidate_response? "" : rejected_reason
      )
      .then(response => {
        if (response.status === 201) {
          this.setState({
            offer: response.data,
            
          });
          this.displayOfferResponse();
        } else if (response.error) {
          this.setState({
            error: response.error
          });
        }
      });
  }
  
  row = ( col1, col2)=>{
    return <div className="row">
              <div class="col-6 font-weight-bold pr-4" align="right">{col1}:</div>
              <div class="col-6 pl-4" align="left">{col2}</div>
            </div>
  }
  
  displayOfferResponse = e =>{
       const { offer } = this.state;
       return (
         <div className="container">
            <p className="h5 pt-5">
                {offer.candidate_response=== true?
                "You have accepted the following offer on  "
                :
                "You have rejected the following offer on "
                }
                {offer.responded_at !== undefined ?offer.responded_at.substring(0,10): "-date-"}.
            </p>

           <div className="white-background card form mt-5">
              {this.row( "Offer date", offer.offer_date !== undefined ? offer.offer_date.substring(0,10): "-date-")}
              {this.row("Offer expiry date",offer.expiry_date !== undefined ? offer.expiry_date.substring(0,10): "-date-")}
              {this.row("Payment", offer.payment_required? "Required": "No payment required")}
              {this.row( "Travel award", offer.travel_award? "Allocated": "Not allocated")}
              {this.row( "Accommodation", offer.accommodation_award? "Allocated": "Not allocated")}
              {!(offer.candidate_response) && <div>{this.row( "Rejection reason", offer.rejected_reason)}</div>}
           </div>
        </div>);
  }

  displayOfferContent = e => {
    const { offer, userProfile, rejected_reason } = this.state;
    return (
    <div>
      { offer.candidate_response !== null ?
        this.displayOfferResponse()
      :
      <div className="container">
        <p className="h5 pt-5">
          We are pleased to offer you a place at the Deep Learning Indaba 2019.
          Please see the details of this offer below{" "}
        </p>

        <form class="form pt-5 ">
          <p className="card p">
            You have been accepted as a{" "}
            {userProfile != null ? userProfile.user_category : "<Category>"}{" "}
          </p>
          <div className="white-background card form">
            <p class="font-weight-bold">Your status</p>
            <div class="row ">
              <div class="col-6 font-weight-bold pr-4"  align="right">Travel Award:</div>
              <div class="col-6 pl-4"  align="left">
                {offer != null
                  ? offer.travel_award
                    ? "Allocated"
                    : "Not Allocated"
                  : "Not available"}
              </div>
            </div>

            <div class="row">
              <div class="col-6 font-weight-bold pr-4"  align="right">Accommodation Award:</div>
              <div class="col-6 pl-4"  align="left">
                {offer != null
                  ? offer.accommodation_award
                    ? "Allocated"
                    : "Not Allocated"
                  : "Not available"}
              </div>
            </div>

            <div class="row pb-5 ">
              <div class="col-6 font-weight-bold pr-4"  align="right">Payment Required:</div>
              <div class="col-6 pl-4"  align="left">
                {offer != null
                  ? offer.payment_required
                    ? "Required"
                    : "Not Required"
                  : "Not available"}
              </div>
            </div>
            <p class="font-weight-bold">
              Please accept or reject this offer by{" "}
              {offer != null ? offer.expiry_date !== undefined ? offer.expiry_date.substring(0,10): "-date-" : "unable to load expiry date"}{" "}
            </p>
            <div class="row">
              <div class="col">
                <button
                  type="button"
                  class="btn btn-danger"
                  id="reject"
                  onClick={() => {
                    this.setState(
                      {
                        showReasonBox: true
                      });
                  }}
                >
                  Reject
                </button>
              </div>
              <div class="col">
                <button
                  type="button"
                  class="btn btn-success"
                  id="accept"
                  onClick={() => {
                    this.setState(
                      {
                        candidate_response: true
                      }
                    );
                    this.buttonSubmit(true)
                  }}
                >
                  Accept
                </button>
              </div>
            </div>

            <div class="form-group">
              {this.state.showReasonBox ? (
                <div class="form-group mr-5  ml-5 pt-5">
                  <textarea
                    class="form-control reason-box pr-5 pl-10"
                    onChange={this.handleChange(rejected_reason)}
                    placeholder="Enter rejection message"
                  />
                  <button
                    type="button"
                    class="btn-apply"
                    align="center"
                    onClick={() => {
                      this.setState(
                        {
                          candidate_response: false,
                          showReasonBox: false
                        },
                        this.buttonSubmit(false)
                      );
                    }}
                  >
                    apply
                  </button>
                </div>
              ) : (
                ""
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
    this.getOffer();
    this.setState({
      loading: false 
    });

    let currentUser = JSON.parse(localStorage.getItem("user"));
    profileService.getUserProfile(currentUser.id).then(results => {
      this.setState({
        userProfile: results,
        loading: false,
        error: results.error
      });
    });
  }

  getOffer() {
    this.setState({ loading: true });
    offerServices.getOffer(DEFAULT_EVENT_ID).then(result => {
      this.setState({
        loading: false,
        offer: result.offer,
        error: result.error
      });
    });
  }

  render() {
    const { loading, offer, error } = this.state;
    const loadingStyle = {
      width: "3rem",
      height: "3rem"
    };

    if (loading) {
      return (
        <div class="d-flex justify-content-center pt-5">
          <div class="spinner-border" style={loadingStyle} role="status">
            <span class="sr-only">Loading...</span>
          </div>
        </div>
      );
    }

    if (error)
      return (
        <div class="alert alert-danger" align="center">
          {error}
        </div>
      );
    else if (offer !== null) return this.displayOfferContent();
    else
      return (
        <div className="h5 pt-5" align="center">
          {" "}
          You are currently on the waiting list for the Deep Learning Indaba
          2019. Please await further communication
        </div>
      );
  }
}

export default withRouter(Offer);
