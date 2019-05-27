import React, { Component } from "react";
import { withRouter } from "react-router";
import { invitedGuestServices } from "../../../services/invitedGuests/invitedGuests.service";

import "react-table/react-table.css";

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

class InvitedGuests extends Component {
  constructor(props) {
    super(props);
    this.state = {
      isLoading: true,
      reviewHistory: [],
      isError: false,
      currentPage : 0,
      defaultPageSize : 10,
      selected: null,
      totalPages: null,
      guestList: [],
    };
  }

  componentDidMount() {
    console.log(DEFAULT_EVENT_ID);
    this.setState({ loading: true });
    invitedGuestServices.getInvitedGuestList(DEFAULT_EVENT_ID).then(result => {
      this.setState({
        loading: false,
        guestList: result.form,
        error: result.error
      });
    });
  }

  render() {
    const {loading, error} = this.state;

    if (loading) {
      return (
        <div class="d-flex justify-content-center">
          <div class="spinner-border" role="status">
            {/* <span class="sr-only">Loading...</span> */}
            <span class="sr-only">Loading...</span>

          </div>
        </div>
      )
    }

    if (error) {
      return <div class="alert alert-danger">Error</div>
    }

    return (
      <div className="ReviewHistory">
        <p className="h5 text-center mb-4">Invited Guests</p>
         {this.state.guestList.map(user => <div>{"Person Name : " + user.user.firstname +" "+ user.user.lastname}</div>)}

         <select>
           <option value="firstOption">First option</option>
           <option value="firstOption">second option</option>

         </select>
      </div>
    );
  }
}

export default withRouter(InvitedGuests);