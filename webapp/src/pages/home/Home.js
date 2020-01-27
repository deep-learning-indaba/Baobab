import React, { Component } from 'react';
import './Home.css';
import { NavLink } from "react-router-dom";
import { eventService } from "../../services/events/events.service";
import { organisationService } from "../../services/organisation/organisation.service";

class Home extends Component {

    constructor(props) {
      super(props);
  
      this.state = {
          events: null,
          organisation: null,
          errors: []
      }
    }
  
    componentDidMount() {
        if (this.props.user) {
            eventService.getEvents().then(response=>{
                if (response.error) {
                    this.setState(prevState=>({
                        errors: [...prevState.errors, response.error]
                    }));
                }
                this.setState({
                    events: response.events,
                });
            });
        }
        
        this.props.setEvent(null, null);

        organisationService.getOrganisation().then(response=>{
            if (response.error) {
                this.setState(prevState=>({
                    errors: [...prevState.errors, response.error]
                }));
            }
            this.setState({
                organisation: response.organisation,
            });
        });

    }

    render() {
        return (
        <div>
            <div>
                <img src={this.state.organisation && require("../../images/" + this.state.organisation.large_logo)} className="img-fluid large-logo" alt="logo" />
            </div>
            {!this.props.user && <div>
                {this.state.organisation && <h2 className="Blurb">Welcome to {this.state.organisation.system_name}</h2>}
                <p class="text-center"><NavLink to="/createAccount">Sign up</NavLink> for an account in order to apply for an event, or <NavLink to="/login">login</NavLink> if you already have one.</p>
            </div>
            }
            
            {this.props.user && <div>
                <h3>Upcoming Events</h3>
                {this.state.events && this.state.events.length > 0 && <table className="event-table">
                    <tbody>
                        {this.state.events.map(e=>{
                            return <tr><td><h5>{e.description}</h5>{e.start_date + " to " + e.end_date}</td><td>{e.status}</td></tr>
                        })}
                    </tbody>
                </table>}
            </div>
            }

        </div>
        );
    }

}

export default Home;