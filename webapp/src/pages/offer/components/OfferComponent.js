import React, {Component} from "react";
import {withRouter} from "react-router";
import { offerServices  } from "../../../services/offer/offer.service";
import { profileService} from "../../../services/profilelist/profilelist.service";

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

class Offer extends Component {
  
  constructor(props) {
        super(props);
  
        this.state = {
          user:{},
          userProfile : [],
          loading: true,
          error: "",
          offer_id: null,
          rejected_reason:"",
          rejected:false,
          showReasonBox:false,
          accepted: false,
          offer: [],
          category:""
        };
      }
    
      
      handleChange = field => {
        return event => {
          this.setState({
            [field.name]: event.target.value
          });
        };
      };

      buttonSubmit(){
         const {offer_id,accepted,rejected,rejected_reason} = this.state;
   
        offerServices.updateOffer(offer_id, DEFAULT_EVENT_ID, accepted, rejected, rejected_reason)
        .then(response=>{
          if (response.msg === "succeeded") {
            this.setState({
              addedSucess: true,
              notFound: false
            });
          } else if (response.error) {
            this.setState({
              addedSucess: false,
              notFound: true
            });
          }
        })
      }
    
    displayOfferContent = (e) => {
      const {offer,userProfile} = this.state;
      return(   
      <div className="container"  align="center" >
      <p className="h5 pt-5">We are pleased to offer you a place at the Deep Learning Indaba 2019. Please see the details of this offer below </p>

      <form class="pt-5 ">
        <p class="font-weight-bold">You have been accepted as a  {userProfile!=null ? userProfile.user_category: "<Category>"} </p>
        <p class="font-weight-bold">Your status</p>
        <div class="row">
          <div class="col-8 font-weight-bold">
            Travel Award:
          </div>
          <div class="col-2">
          {offer != null
              ? offer.travel_award
              ? "True"
              : "not active"
              : "Not available"}
          </div>
        </div>

        <div class="row">
          <div class="col-8 font-weight-bold">
            Accommodation Award:
          </div>
          <div class="col-2">
          {offer!=null
          ? offer.accomodation_award
          ? "True"
          : "not active"
          : "Not available"}
          </div>
        </div>

        <div class="row pb-5 ">
          <div class="col-8 font-weight-bold">
            Payment Required:
          </div>
          <div class="col-2">
          {offer!=null
          ? offer.payment_required
          ? "True"
          : "not required"
          : "Not available"}
          </div>
        </div>
        <p class="font-weight-bold">Please accept or reject this offer by {offer!=null ? offer.expiry_date : "unable to load expiry date"} </p>
        <div class="row">
         <div class="col">
          <button type="button" class="btn btn-danger" id="reject"onClick={
            ()=>{
              this.setState({
                rejected:true,
                showReasonBox:true
              },
              this.buttonSubmit());
            }
          } >
              Reject
          </button>
          </div>
          <div class="col">
          <button type="button" class="btn btn-success" id="accept" onClick={()=>{
              this.setState({
                accepted:true
              },
              this.buttonSubmit());
          }}>
              Accept
          </button>
          </div>
        </div> 

        <div class="form-group">
         { this.state.showReasonBox ? 
          <div class="form-group mr-5  ml-5 pt-5" >
          <textarea class="form-control pr-5 pl-10" id="textArea" onChange={()=>{this.handleChange(this.rejected_reason)}}  placeholder="Enter rejection message"></textarea>
          <button type="button" class="btn" id="apply" onClick={ ()=>{
              this.setState({
                showReasonBox:false
              },
              this.buttonSubmit());
            }}>apply</button>
        </div>
        :""
        }
        </div>
      
      </form>
    </div>
      )}


    componentWillMount() {
          this.getOffer();
          this.setState({
            
            loading: false,
            buttonLoading: false
          });

          let currentUser = JSON.parse(localStorage.getItem("user"));
          profileService.getUserProfile(currentUser.id)
          .then(results => {
            this.setState(
              {
                userProfile: results,
                loading: false,
                error: results.error
              });
          });       
      }
   
      getOffer(){
        this.setState({loading:true});
        offerServices.getOffer(DEFAULT_EVENT_ID).then(result => {
          this.setState({
            loading:false,
            offerList:result.offer,
            error:result.error
          });
          });
      }
      
    render(){
      const {loading, offer, error} = this.state;
      const loadingStyle = {
        "width": "3rem",
        "height": "3rem"
      }

      if (loading) {
        return (
          <div class="d-flex justify-content-center pt-5">
            <div class="spinner-border" style={loadingStyle} role="status">
              <span class="sr-only">Loading...</span>
            </div>
          </div>
        )
      }

        if (error)
         return <div class="alert alert-danger" align="center">{error}</div>
        else 
        if (offer!==null) 
          return this.displayOfferContent();
        else
          return <div className="h5 pt-5" align="center"> You are currently on the waiting list for the Deep Learning Indaba 2019. Please await further communication</div>
   }
}

export default withRouter(Offer);
