import React, { Component } from "react";
import { withRouter } from "react-router";
import { offerServices } from "../../../services/offer/offer.service";
import { profileService } from "../../../services/profilelist/profilelist.service";
import { NavLink } from "react-router-dom";

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
      offer: null,
      noOffer: null,
      category: "",
      accepted_accommodation_award: false,
      accepted_travel_award: false
    };
  }
  
  resetPage =()=>{
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
    const { offer, rejected_reason,accepted_accommodation_award,accepted_travel_award } = this.state;
      
      if(candidate_response !== null){
        offerServices
          .updateOffer(
            offer.id,
            DEFAULT_EVENT_ID,
            candidate_response,
            candidate_response? "" : rejected_reason,
            accepted_accommodation_award,
            accepted_travel_award
          )
          .then(response => {
            if (response.response && response.response.status === 201) {
              this.setState({
                offer: response.response.data, 
                showReasonBox: false
              }, () => {
                this.displayOfferResponse();
                if (candidate_response) {
                  this.props.history.push("/registration");
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
  
  row = ( col1, col2)=>{
    return <div className="row">
              <div class="col-6 font-weight-bold pr-4" align="right">{col1}:</div>
              <div class="col-6 pl-4" align="left">{col2}</div>
            </div>
  }

  onChangeAccommodation=()=>{
      this.setState({
        accepted_accommodation_award: !this.state.accepted_accommodation_award
      });
  }
  onChangeTravel=()=>{
    this.setState({
      accepted_travel_award: !this.state.accepted_travel_award
    });
  }
  
  displayOfferResponse = ()=>{
       const { offer } = this.state;
       let responded_date = offer.responded_at !== undefined ?offer.responded_at.substring(0,10): "-date-"
       return (
         <div className="container">
            <p className="h5 pt-5">
                {offer.candidate_response && <span>You accepted the following offer on {responded_date}.</span>}
                {!offer.candidate_response && <span class="text-danger">You rejected your offer for a spot at the Indaba on {responded_date} for the following reason:<br/><br/>{offer.rejected_reason}</span>}
            </p>

           {offer.candidate_response && <div className="white-background card form mt-5">
              {this.row("Offer date", offer.offer_date !== undefined ? offer.offer_date.substring(0,10): "-date-")}
              {this.row("Offer expiry date",offer.expiry_date !== undefined ? offer.expiry_date.substring(0,10): "-date-")}
              {this.row("Registration fee", offer.payment_required? "Payment of 350 USD Required to confirm your place": "Fee Waived")}
              {this.row("Travel", offer.accepted_travel_award? "Your travel to and from Nairobi will be arranged by the Indaba": "You are responsible for your own travel to and from Nairobi.")}
              {this.row("Accommodation", offer.accepted_accommodation_award? "Your accommodation will be covered by the Indaba in a shared hostel from the 25th to 31st August": "You are responsible for your own accommodation in Nairobi.")}
           </div>}
          
            {offer.candidate_response && <div className="row mt-4">
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
                  }}
                >
                  Reject
                </button>
              </div>
              <div className="col">
              <NavLink className="btn btn-primary" to="/registration">
                  Proceed to Registration >
              </NavLink>
              </div>
            </div>
            }
            {this.state.showReasonBox &&
                <div className="row">
                  <textarea
                    class="form-control reason-box pr-5 pl-10 pb-5"
                    onChange={this.handleChange(this.state.rejected_reason)}
                    placeholder="Enter rejection message"
                  />
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
                    }}
                  >
                    Submit
                  </button>
                </div>
            }
        </div>);
  }



  displayOfferContent = e => {
    const { offer, userProfile, rejected_reason,accepted_accommodation_award,accepted_travel_award } = this.state;
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

        <form class="form pt-2 ">
          <p className="card p">
            You have been accepted as a{" "}
            {userProfile != null ? userProfile.user_category : "<Category>"}{" "}
          </p>
          <div className="white-background card form">
            <p class="font-weight-bold">Offer Details</p>
            <div class="row mb-4">
              <div class="col-md-3 font-weight-bold pr-2" align="center">Travel:</div>
              <div class="col-md-6" align="left">
                {offer && offer.travel_award && accepted_travel_award &&
                  "We are pleased to offer you a travel award which will cover your flights to and from Nairobi."}
                {offer && offer.travel_award && !accepted_travel_award && 
                  <span class="text-danger">You have chosen to reject the travel award - you will be responsible for your own travel to and from Nairobi!</span>
                }
                {offer && offer.requested_travel && !offer.travel_award && 
                  "Unfortunately we are unable to grant you the travel award you requested in your application."}
                {offer && !offer.requested_travel && !offer.travel_award &&
                  "You did not request a travel award. You will be responsible for your own travel to and from Nairobi"}
                
              </div>
              <div class="col-md-3">
                  {offer.travel_award && <div class="form-check">
                      <input type="checkbox" class="form-check-input" checked={accepted_travel_award} onChange={this.onChangeTravel}
                        id="CheckTravel" />
                      <label class="form-check-label" for="CheckTravel">I accept the travel award.</label>
                    </div>}
              </div>
            </div>

            <div class="row mb-2">
              <div class="col-md-3 font-weight-bold pr-2"  align="center">Accommodation:</div>
              <div class="col-md-6"  align="left">
                {offer && offer.accommodation_award && accepted_accommodation_award &&
                  "We are pleased to offer you an accommodation award which will cover your stay between the 25th and 31st of August. Note that this will be in a shared hostel room (with someone of the same gender) at Kenyatta university."}
                {offer && offer.accommodation_award && !accepted_accommodation_award && 
                  <span class="text-danger">You have chosen to reject the accommodation award - you will be responsible for your own accommodation in Nairobi during the Indaba!</span>
                }
                {offer && offer.requested_accommodation && !offer.accommodation_award && 
                  <span>Unfortunately we are unable to grant you the accomodation award you requested in your application. 
                    We do however have reasonably priced accommodation available in shared hostel rooms on campus, available on a first come first serve basis. Please see <a href="www.deeplearningindaba.com/accommodation-2019">here</a> for more details
                  </span>}
                {offer && !offer.requested_accommodation && !offer.accommodation_award &&
                  "You did not request an accommodation award. You will be responsible for your own accommodation during the Indaba."}
              </div>
              <div class="col-md-3">
                {offer.accommodation_award && <div class="form-check accommodation-container">
                  <input type="checkbox" class="form-check-input" checked={accepted_accommodation_award} onChange={this.onChangeAccommodation} 
                    id="CheckAccommodation" />
                  <label class="form-check-label" for="CheckAccommodation">I accept the accommodation award.</label>
                </div>}
              </div>
              
            </div>

            <div class="row mb-3">
              <div class="col-md-3 font-weight-bold pr-2" align="center">Registration Fee:</div>
              <div class="col-md-6" align="left">
                {offer && offer.payment_required && "In order to confirm your place, you will be liable for a 350 USD registration fee."}
                {offer && !offer.payment_required && "Your registration fee has been waived."}
              </div>
            </div>

            <p class="font-weight-bold">
              Please accept or reject this offer by{" "}
              {offer != null ? offer.expiry_date !== undefined ? offer.expiry_date.substring(0,10): "-date-" : "unable to load expiry date"}{" "}
            </p>
           
            <div class="form-group">
              {this.state.showReasonBox ? (
                <div class="form-group mr-5  ml-5 pt-5">
                  <textarea
                    class="form-control reason-box pr-5 pl-10 pb-5"
                    onChange={this.handleChange(rejected_reason)}
                    placeholder="Enter rejection message"
                  />
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
                    }}
                  >
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
                        this.setState(
                          {
                            showReasonBox: true
                          });
                      }}
                    >
                      Reject
                    </button>
                  </div>
                  <div class="col" align="center">
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
              )}
            </div>
          </div>
        </form>
      </div>
      }
    </div>
    );
  };

  componentWillMount = () => {
    let currentUser = JSON.parse(localStorage.getItem("user"));
    profileService.getUserProfile(currentUser.id).then(results => {
      this.setState({
        userProfile: results,
        error: results.error
      }, this.getOffer);
    });
  }

  getOffer = () => {
    this.setState({ loading: true });
    offerServices.getOffer(DEFAULT_EVENT_ID).then(result => {
      if (result.error && result.statusCode === 404) {
        this.setState({
          noOffer: true,
          loading: false
        });
      }
      else if (result.error) {
        this.setState({
          error: result.error,
          loading: false
        });
      }
      else {
        this.setState({
          loading: false,
          offer: result.offer,
          error: result.error,
          accepted_travel_award: result.offer.accommodation_award,
          accepted_travel_award: result.offer.travel_award
        });
      }
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
