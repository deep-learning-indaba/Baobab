import React, { Component } from 'react';
import logo from '../../images/indaba-logo-dark.png';
import './Home.css';
import { applicationFormService } from "../../services/applicationForm";
import { offerServices } from "../../services/offer/offer.service";
import { NavLink } from "react-router-dom";
import { invitedGuestServices } from '../../services/invitedGuests/invitedGuests.service';
import CookieConsent from "react-cookie-consent";

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

const headings = ["Event", "Start date", "End date", "Status"];
// const fieldNames = ["description", "start_date", "end_date", "status"]; unused

class Home extends Component {

  constructor(props) {
    super(props);

    this.state = {
      headings: headings,
      rows: [],
      applicationStatus: null,
      offer: null
    }
  }

  componentDidMount() {
    // Temporarily removed during campaign to get people to complete their applications
    // getEvents().then(response => {
    //   if (response) {
    //     this.setState({
    //       headings: headings,
    //       rows: response
    //     })
    //   }
    // });

    // Only check for response/offer/invited guest if user is logged in
    const user = localStorage.getItem('user');
    if (!user)
      return 

    applicationFormService.getResponse(DEFAULT_EVENT_ID).then(resp => {
      let applicationStatus = null;
      if (resp.response) {
        if (resp.response.is_submitted) {
          applicationStatus = "Submitted";
        }
        else if (resp.response.is_withdrawn) {
          applicationStatus = "Withdrawn";
        }
        else {
          applicationStatus = "NOT Submitted";
        }
        this.setState({
          applicationStatus: applicationStatus
        })
      }
      else {
        this.setState({
          applicationStatus: "Not Started"
        });
      }
    });

    offerServices.getOffer(DEFAULT_EVENT_ID).then(result => {
      this.setState({
        offer: result.offer
      });
    });

    invitedGuestServices.determineIfInvitedGuest(DEFAULT_EVENT_ID).then(response => {
      if (response.statusCode === "200") {
        this.setState({
          invitedGuest: true
        });
      }
      else if (response.statusCode === "404") {
        this.setState({
          invitedGuest: false
        });
      }
    })

  }

  render() {
    // if (this.state.rows && this.state.rows.length > 0) {
    //   const theadMarkup = (
    //     <tr>
    //       {this.state.headings.map((_cell, cellIndex) => {
    //         return (
    //           <th className="Cell">
    //             {this.state.headings[cellIndex]}
    //           </th>
    //         )
    //       })}
    //     </tr>
    //   );

    //   const tbodyMarkup = this.state.rows.map((_row, rowIndex) => {
    //     return (
    //       <tr>
    //         {fieldNames.map((_cell, cellIndex) => {
    //           return (
    //             <td className="Cell">
    //               {
    //                 this.state.rows[rowIndex][fieldNames[cellIndex]] === "Apply now" || 
    //                   this.state.rows[rowIndex][fieldNames[cellIndex]] === "Continue application" ?
    //                   <NavLink to="/applicationForm">{this.state.rows[rowIndex][fieldNames[cellIndex]]}</NavLink> :
    //                   this.state.rows[rowIndex][fieldNames[cellIndex]]
    //               }
    //             </td>
    //           )
    //         })}
    //       </tr>
    //     )
    //   });

    // }

    let statusClass = this.state.applicationStatus === "Submitted" 
      ? this.state.offer === null ? "text-warning" : "text-success" 
      : "text-danger"
    // TODO change Baobab to [event]
    return (
      <div >
        <div>
          <img src={logo} className="img-fluid" alt="logo" />
        </div>
        {this.props.user && this.state.applicationStatus && <h3 className="Blurb">Application Status for Deep Learning Indaba 2019</h3>}
        {!this.props.user && <h2 className="Blurb">Welcome to Baobab</h2>}

        {(this.props.user && this.state.applicationStatus) &&
          <div>
            <div class="status2019 row text-center">
              <div className="col-sm">
                <h5 className={statusClass}>

                  {this.state.applicationStatus === "Submitted" && this.state.offer && <span>
                    Your application was successful!
                  </span>}

                  {this.state.applicationStatus === "Submitted" && !this.state.offer && this.state.invitedGuest !== true && <span>
                    Waiting List
                  </span>}

                  {this.state.applicationStatus !== "Submitted" && this.state.invitedGuest === true && <span>
                    You've been invited as a guest!
                  </span>}

                  {this.state.applicationStatus !== "Submitted" && this.state.invitedGuest !== true && this.state.applicationStatus}
                </h5>

                {this.state.invitedGuest === true && <div>
                  <p>You've been invited to the Indaba as a guest! Please proceed to registration <NavLink to="/registration">here</NavLink>.</p>
                </div>}


                {this.state.applicationStatus === "Submitted" &&
                <div>
                  {this.state.offer !== null ? <p>There is an offer waiting for you, <NavLink to="/offer">click here</NavLink> to view it.</p>
                  : <p>You are currently on the waiting list for the Deep Learning Indaba 2019. Please await further communication.</p>}
                </div>}

                {this.state.applicationStatus === "Withdrawn" && <p>
                  Your application has been withdrawn - you will not be considered for a place at the Indaba.
                </p>}

                {this.state.applicationStatus === "NOT Submitted" && <p>
                  You did not submit an application to attend the Deep Learning Indaba 2019!
                </p>}


                {this.state.applicationStatus === "Not Started" && this.state.invitedGuest !== true  && <p>
                  You did not apply to attend the Deep Learning Indaba 2019.
                </p>}

              </div>
            </div>
          </div>
        }

        {!this.props.user &&
          <p class="text-center"><NavLink to="/createAccount">Sign up</NavLink> for an account in order to apply for an Indaba event, or <NavLink to="/login">login</NavLink> if you already have one.</p>}
        {
          //Temporarily removed during campaign to get people to complete their applications
          //this.props.user && table
        }
        <CookieConsent
          cookieName="sweetIndabaCookie"
          style={{ background: "#343a40" }}
          buttonStyle={{ fontWeight: "bold" }}
          enableDeclineButton
          declineButtonText="Decline"
          buttonText="I accept"
          buttonClasses="btn btn-primary"
          containerClasses="alert alert-warning col-lg-12"
          contentClasses="text-capitalize"
        > By accepting you agree to our use of cookies and other technologies to process your personal data to give you better functionality and to ensure your experience is consistent between visits.  <a href="/PrivacyPolicy.pdf" style={{ color: "white" }}>Learn more >></a>
        </CookieConsent>
      </div>
    );
  }
}

export default Home;
