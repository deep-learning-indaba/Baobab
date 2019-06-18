import React, { Component } from 'react';
import logo from '../../images/indaba-logo-dark.png';
import './Home.css';
import { getEvents } from "../../services/events";
import { applicationFormService } from "../../services/applicationForm";
import { offerServices } from "../../services/offer/offer.service";
import { NavLink } from "react-router-dom";

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

const headings = ["Event", "Start date", "End date", "Status"];
const fieldNames = ["description", "start_date", "end_date", "status"];

class Home extends Component {

  constructor(props) {
    super(props);

    this.state = {
      headings: headings,
      rows: [],
      applicationStatus: null,
      offer:null
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
  
  }

  render() {
    let table = (<div></div>)

    if (this.state.rows && this.state.rows.length > 0) {
      const theadMarkup = (
        <tr>
          {this.state.headings.map((_cell, cellIndex) => {
            return (
              <th className="Cell">
                {this.state.headings[cellIndex]}
              </th>
            )
          })}
        </tr>
      );

      const tbodyMarkup = this.state.rows.map((_row, rowIndex) => {
        return (
          <tr>
            {fieldNames.map((_cell, cellIndex) => {
              return (
                <td className="Cell">
                  {
                    this.state.rows[rowIndex][fieldNames[cellIndex]] === "Apply now" || 
                      this.state.rows[rowIndex][fieldNames[cellIndex]] === "Continue application" ?
                      <NavLink to="/applicationForm">{this.state.rows[rowIndex][fieldNames[cellIndex]]}</NavLink> :
                      this.state.rows[rowIndex][fieldNames[cellIndex]]
                  }
                </td>
              )
            })}
          </tr>
        )
      });

      table = this.state.rows ? (
        <table align="center" className="Table">
          <thead>{theadMarkup}</thead>
          <tbody>{tbodyMarkup}</tbody>
        </table>
      ) : (<div></div>)
    }

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
                <h4 className={this.state.applicationStatus == "Submitted" ? "text-success" : "text-danger"}>
                  {this.state.applicationStatus}
                </h4>

                {this.state.applicationStatus == "Submitted" &&
                <div>
                  <p>
                    Thank you! Your application has been received and is under review. You can expect to hear our decision mid-June.
                  </p>
                  {this.state.offer !== null ? <p>There is an offer waiting for you, <NavLink to="/offer">click here</NavLink> to view it.</p>
                  : <p>You are currently on the waiting list for the Deep Learning Indaba 2019. Please await further communication.</p>}
                </div>}
                {this.state.applicationStatus == "Withdrawn" && <p>
                  Your application has been withdrawn - you will not be considered for a place at the Indaba.
                </p>}
                {this.state.applicationStatus == "NOT Submitted" && <p>
                  You have NOT submitted your application! <NavLink to="/applicationForm">Complete and submit</NavLink> it before 26 May to be considered for a place at the Indaba.
                </p>}
                {this.state.applicationStatus == "Not Started" && <p>
                  We have not received an application from you. <NavLink to="/applicationForm">Complete it</NavLink> before 26 May to be considered for a place at the Indaba.
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
      </div>
    );
  }
}

export default Home;
