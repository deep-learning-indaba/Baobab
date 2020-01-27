import React, { Component } from "react";
import { Router, Route, NavLink, Switch } from "react-router-dom";
import Home from "./pages/home";
import EventHome from "./pages/eventHome";
import Login from "./pages/login";
import ResetPassword from "./pages/resetPassword";
import CreateAccount from "./pages/createAccount";
import VerifyEmail from "./pages/verifyEmail";
import Profile from "./pages/profile";
import { PrivateRoute } from "./components";
import UserDropdown from "./components/User";

import ReactGA from "react-ga";
import "./App.css";
import history from "./History";
import { organisationService } from "./services/organisation/organisation.service";

ReactGA.initialize("UA-136093201-1", {
  debug: false,
  testMode: process.env.NODE_ENV === "test"
});

ReactGA.pageview(window.location.pathname + window.location.search);
history.listen((location) => {
  ReactGA.pageview(location.pathname + location.search);
});


class EventNav extends Component {
  constructor(props) {
    super(props);

    this.state = {
      collapsed: true
    };
  }

  isEventAdmin = user => {
    if (!user) {
      return false;
    }
    return (
      user.is_admin || (user.roles && user.roles.some(r => r.role === "admin"))
    );
  };

  isRegistrationAdmin = user => {
    if (!user) {
      return false;
    }
    return (
      user.is_admin ||
      (user.roles &&
        user.roles.some(
          r => r.role === "admin" || r.role === "registration-admin"
        ))
    );
  };

  isRegistrationVolunteer = user => {
    if (!user) {
      return false;
    }
    return (
      user.is_admin ||
      (user.roles &&
        user.roles.some(
          r => r.role === "admin" || r.role === "registration-admin" || r.role === "registration-volunteer"
        ))
    );
  };

  isEventReviewer = user => {
    if (!user) {
      return false;
    }
    return user.roles && user.roles.some(r => r.role === "reviewer");
  };

  render() {
    return (
    <ul className="navbar-nav mr-auto">
      <li className={"nav-item"}>
        <NavLink
          exact
          to="/"
          activeClassName="nav-link active"
          className="nav-link"
          onClick={this.props.toggleMenu}
        >
          Home
        </NavLink>
      </li>
      {this.props.user && (
        <li className="nav-item">
          <NavLink
            to="/applicationForm"
            activeClassName="nav-link active"
            className="nav-link"
            onClick={this.props.toggleMenu}
          >
            Apply
          </NavLink>
        </li>
      )}
      {this.props.user && (
      <li className="nav-item">
        <NavLink
          to="/offer"
          activeClassName="nav-link active"
          className="nav-link"
          onClick={this.props.toggleMenu}
        >
          Offer
        </NavLink>
      </li>
      )}
      {this.props.user && (
        <li className="nav-item dropdown ">
          <div
            className="nav-link dropdown-toggle link-style"
            id="navbarDropdown"
            role="button"
            data-toggle="dropdown"
            aria-haspopup="true"
            aria-expanded="false"
          >
            Registration
          </div>
          <div className="dropdown-menu" aria-labelledby="navbarDropdown">
            <NavLink
              to="/registration"
              className="dropdown-item"
              onClick={this.props.toggleMenu}
            >
              Registration Form
            </NavLink>
            <NavLink
              to="/invitationLetter"
              className="dropdown-item"
              onClick={this.props.toggleMenu}
            >
              Invitation Letter
            </NavLink>
            {this.isRegistrationVolunteer(this.state.user) && 
              <NavLink
                to="/eventAttendance"
                className="dropdown-item"
                onClick={this.props.toggleMenu}
              >
                Event Attendance
              </NavLink>
            }
          </div>
        </li>
      )}
      {this.isEventAdmin(this.props.user) && (
        <li className="nav-item dropdown">
          <div
            className="nav-link dropdown-toggle link-style"
            id="navbarDropdown"
            role="button"
            data-toggle="dropdown"
            aria-haspopup="true"
            aria-expanded="false"
          >
            Event Admin
          </div>
          <div className="dropdown-menu" aria-labelledby="navbarDropdown">
            <NavLink
              to="/eventStats"
              className="dropdown-item"
              onClick={this.props.toggleMenu}
            >
              Event Stats
            </NavLink>
            <NavLink
              to="/reviewAssignment"
              className="dropdown-item"
              onClick={this.props.toggleMenu}
            >
              Review Assignment
            </NavLink>
            <NavLink
              to="/invitedGuests"
              className="dropdown-item"
              onClick={this.props.toggleMenu}
            >
              Invited Guests
            </NavLink>
            <NavLink
              to="/profile-list"
              className="dropdown-item"
              onClick={this.props.toggleMenu}
            >
              Applicant Profiles
            </NavLink>
          </div>
        </li>
      )}
      {this.isEventReviewer(this.props.user) && (
        <li className="nav-item dropdown">
          <div
            className="nav-link dropdown-toggle link-style"
            id="navbarDropdown"
            role="button"
            data-toggle="dropdown"
            aria-haspopup="true"
            aria-expanded="false"
          >
            Reviews
          </div>
          <div className="dropdown-menu" aria-labelledby="navbarDropdown">
            <NavLink
              to="/review"
              className="dropdown-item"
              onClick={this.props.toggleMenu}
            >
              Review
            </NavLink>
            <NavLink
              to="/reviewHistory"
              className="dropdown-item"
              onClick={this.props.toggleMenu}
            >
              Review History
            </NavLink>
          </div>
        </li>
      )}
      {this.isRegistrationAdmin(this.props.user) && (
        <li className="nav-item dropdown">
          <div
            className="nav-link dropdown-toggle link-style"
            id="navbarDropdown"
            role="button"
            data-toggle="dropdown"
            aria-haspopup="true"
            aria-expanded="false"
          >
            Registration Admin
          </div>
          <div className="dropdown-menu" aria-labelledby="navbarDropdown">
            <NavLink
              to="/registrationAdmin"
              className="dropdown-item"
              onClick={this.props.toggleMenu}
            >
              Unconfirmed Registrations
            </NavLink>
          </div>
        </li>
      )}
    </ul>
    )
  }
}

class App extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: {},
      organisation: null,
      collapsed: true,
      eventKey: null,
      event: null
    };

    this.refreshUser = this.refreshUser.bind(this);
  }

  componentDidMount() {
    this.setState({
      user: JSON.parse(localStorage.getItem("user"))
    });

    organisationService.getOrganisation().then(response => {
      this.setState({
        organisation: response.organisation,
        error: response.error
      });
    });
  }

  refreshUser() {
    this.setState({
      user: JSON.parse(localStorage.getItem("user"))
    });
  }

  toggleMenu = () => {
    this.setState({ collapsed: !this.state.collapsed });
  };

  setEvent = (eventKey, event) => {
    this.setState({
      eventKey: eventKey,
      event: event
    });
  }

  render() {
    return (
      <Router history={history}>
        <div>
          <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
            <a className="navbar-brand" href="/">
              <img
                src={this.state.organisation && require("./images/" + this.state.organisation.small_logo)}
                width="30"
                height="30"
                className="d-inline-block align-top brand-image"
                alt=""
              />
              {this.state.organisation && this.state.organisation.system_name}
            </a>
            <button
              className="navbar-toggler"
              type="button"
              data-toggle="collapse"
              data-target="#navbarNav"
              aria-controls="navbarNav"
              aria-expanded="false"
              aria-label="Toggle navigation"
            >
              <span className="navbar-toggler-icon" />
            </button>
            <div
              class={
                "collapse navbar-collapse" +
                (this.state.collapsed ? " collapsed" : "")
              }
              id="navbarNav"
            >
              {this.state.currentEvent && <EventNav eventKey={this.state.eventKey} event={this.state.event}/>}
              <UserDropdown
                logout={this.refreshUser}
                user={this.state.user}
                onClick={this.toggleMenu}
              />
            </div>
          </nav>
          <div className="Body">
            <div className="container-fluid">
              <Switch>
                <Route
                  exact
                  path="/"
                  render={props => <Home {...props} user={this.state.user} setEvent={this.setEvent}/>}
                />
                <Route
                  exact
                  path="/login"
                  render={props => (
                    <Login {...props} loggedIn={this.refreshUser} />
                  )}
                />
                <Route
                  exact
                  path="/createAccount"
                  render={props => (
                    <CreateAccount {...props} loggedIn={this.refreshUser} />
                  )}
                />
                <Route
                  exact
                  path="/resetPassword"
                  render={props => (
                    <ResetPassword {...props} loggedIn={this.refreshUser} />
                  )}
                />
                <Route exact path="/verifyEmail" component={VerifyEmail} />
                <PrivateRoute exact path="/profile" component={Profile} />
                <PrivateRoute 
                  path="/:eventKey" 
                  component={EventHome} 
                  setEvent={this.setEvent}
                /> 
              </Switch>
            </div>
          </div>
          <footer className="text-muted">
            <div className="container-flex">
              <div>
                {this.state.organisation && this.state.organisation.system_name}, © 2020 |{" "}
                <a href={this.state.organisation && this.state.organisation.url}>
                {this.state.organisation && this.state.organisation.name}
                </a>{" "}
                |{" "}
                <a href="/PrivacyPolicy.pdf" target="_blank">
                  Privacy Policy
                </a>
                {this.state.organisation && this.state.organisation.system_name !== "Baobab" && 
                  <div className="float-right">
                    Powered by <a href="http://www.deeplearningindaba.com" target="_blank" rel="noopener noreferrer">Baobab</a>
                  </div>
                }
              </div>
            </div>
          </footer>
        </div>
      </Router>
    );
  }
}

export default App;
