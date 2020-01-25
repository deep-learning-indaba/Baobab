import React, { Component } from "react";
import { Router, Route, NavLink, Switch } from "react-router-dom";
import Home from "./pages/home";
import Login from "./pages/login";
import ResetPassword from "./pages/resetPassword";
import CreateAccount from "./pages/createAccount";
import Application from "./pages/applicationForm";
import Review from "./pages/review";
import VerifyEmail from "./pages/verifyEmail";
import Profile from "./pages/profile";
import ReviewAssignment from "./pages/reviewAssignment";
import ReviewHistory from "./pages/reviewHistory";
import EventStats from "./pages/eventStats";
import ProfileList from "./pages/profileList";
import ViewProfile from "./pages/viewprofile";
import { PrivateRoute } from "./components";
import UserDropdown from "./components/User";
import InvitedGuests from "./pages/invitedGuests";
import CreateInvitedGuests from "./pages/createInvitedGuest";
import Registration from "./pages/registration";
import InvitedLetter from "./pages/invitationLetter";
import RegistrationAdmin from "./pages/registrationAdmin";
import Attendance from "./pages/attendance/Attendance";
import Offer from "./pages/offer";
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


class App extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: {},
      organisation: null,
      collapsed: true
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
      <Router history={history}>
        <div>
          <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <a class="navbar-brand" href="/">
              <img
                src={this.state.organisation && require("./images/" + this.state.organisation.small_logo)}
                width="30"
                height="30"
                class="d-inline-block align-top"
                alt=""
              />
              {this.state.organisation && this.state.organisation.system_name}
            </a>
            <button
              class="navbar-toggler"
              type="button"
              data-toggle="collapse"
              data-target="#navbarNav"
              aria-controls="navbarNav"
              aria-expanded="false"
              aria-label="Toggle navigation"
            >
              <span class="navbar-toggler-icon" />
            </button>
            <div
              class={
                "collapse navbar-collapse" +
                (this.state.collapsed ? " collapsed" : "")
              }
              id="navbarNav"
            >
              <ul class="navbar-nav mr-auto">
                <li class={"nav-item"}>
                  <NavLink
                    exact
                    to="/"
                    activeClassName="nav-link active"
                    className="nav-link"
                    onClick={this.toggleMenu}
                  >
                    Home
                  </NavLink>
                </li>
                {this.state.user && (
                  <li class="nav-item">
                    <NavLink
                      to="/applicationForm"
                      activeClassName="nav-link active"
                      className="nav-link"
                      onClick={this.toggleMenu}
                    >
                      Apply
                    </NavLink>
                  </li>
                )}
                {this.state.user && (
                <li class="nav-item">
                  <NavLink
                    to="/offer"
                    activeClassName="nav-link active"
                    className="nav-link"
                    onClick={this.toggleMenu}
                  >
                    Offer
                  </NavLink>
                </li>
                )}
                {this.state.user && (
                  <li class="nav-item dropdown ">
                    <div
                      class="nav-link dropdown-toggle link-style"
                      id="navbarDropdown"
                      role="button"
                      data-toggle="dropdown"
                      aria-haspopup="true"
                      aria-expanded="false"
                    >
                      Registration
                    </div>
                    <div class="dropdown-menu" aria-labelledby="navbarDropdown">
                      <NavLink
                        to="/registration"
                        className="dropdown-item"
                        onClick={this.toggleMenu}
                      >
                        Registration Form
                      </NavLink>
                      <NavLink
                        to="/invitationLetter"
                        className="dropdown-item"
                        onClick={this.toggleMenu}
                      >
                        Invitation Letter
                      </NavLink>
                      {this.isRegistrationVolunteer(this.state.user) && 
                        <NavLink
                          to="/eventAttendance"
                          className="dropdown-item"
                          onClick={this.toggleMenu}
                        >
                          Event Attendance
                        </NavLink>
                      }
                    </div>
                  </li>
                )}
                {this.isEventAdmin(this.state.user) && (
                  <li class="nav-item dropdown">
                    <div
                      class="nav-link dropdown-toggle link-style"
                      id="navbarDropdown"
                      role="button"
                      data-toggle="dropdown"
                      aria-haspopup="true"
                      aria-expanded="false"
                    >
                      Event Admin
                    </div>
                    <div class="dropdown-menu" aria-labelledby="navbarDropdown">
                      <NavLink
                        to="/eventStats"
                        className="dropdown-item"
                        onClick={this.toggleMenu}
                      >
                        Event Stats
                      </NavLink>
                      <NavLink
                        to="/reviewAssignment"
                        className="dropdown-item"
                        onClick={this.toggleMenu}
                      >
                        Review Assignment
                      </NavLink>
                      <NavLink
                        to="/invitedGuests"
                        className="dropdown-item"
                        onClick={this.toggleMenu}
                      >
                        Invited Guests
                      </NavLink>
                      <NavLink
                        to="/profile-list"
                        className="dropdown-item"
                        onClick={this.toggleMenu}
                      >
                        Applicant Profiles
                      </NavLink>
                    </div>
                  </li>
                )}
                {this.isEventReviewer(this.state.user) && (
                  <li class="nav-item dropdown">
                    <div
                      class="nav-link dropdown-toggle link-style"
                      id="navbarDropdown"
                      role="button"
                      data-toggle="dropdown"
                      aria-haspopup="true"
                      aria-expanded="false"
                    >
                      Reviews
                    </div>
                    <div class="dropdown-menu" aria-labelledby="navbarDropdown">
                      <NavLink
                        to="/review"
                        className="dropdown-item"
                        onClick={this.toggleMenu}
                      >
                        Review
                      </NavLink>
                      <NavLink
                        to="/reviewHistory"
                        className="dropdown-item"
                        onClick={this.toggleMenu}
                      >
                        Review History
                      </NavLink>
                    </div>
                  </li>
                )}
                {this.isRegistrationAdmin(this.state.user) && (
                  <li class="nav-item dropdown">
                    <div
                      class="nav-link dropdown-toggle link-style"
                      id="navbarDropdown"
                      role="button"
                      data-toggle="dropdown"
                      aria-haspopup="true"
                      aria-expanded="false"
                    >
                      Registration Admin
                    </div>
                    <div class="dropdown-menu" aria-labelledby="navbarDropdown">
                      <NavLink
                        to="/registrationAdmin"
                        className="dropdown-item"
                        onClick={this.toggleMenu}
                      >
                        Unconfirmed Registrations
                      </NavLink>
                    </div>
                  </li>
                )}
              </ul>
              <UserDropdown
                logout={this.refreshUser}
                user={this.state.user}
                onClick={this.toggleMenu}
              />
            </div>
          </nav>
          <div class="Body">
            <div className="container-fluid">
              <Switch>
                <Route
                  exact
                  path="/"
                  render={props => <Home {...props} user={this.state.user} />}
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
                  exact
                  path="/invitationLetter"
                  component={InvitedLetter}
                />
                <PrivateRoute
                  exact
                  path="/applicationForm"
                  component={Application}
                />
                <PrivateRoute
                  exact
                  path="/eventAttendance"
                  component={Attendance}
                />
                <PrivateRoute exact path="/eventStats" component={EventStats} />
                <PrivateRoute
                  exact
                  path="/reviewAssignment"
                  component={ReviewAssignment}
                />
                <PrivateRoute
                  exact
                  path="/reviewHistory"
                  component={ReviewHistory}
                />
                <PrivateRoute
                  exact
                  path="/invitedGuests"
                  component={InvitedGuests}
                />
                <PrivateRoute
                  exact
                  path="/invitedGuests/create"
                  component={CreateInvitedGuests}
                />
                <PrivateRoute exact path="/review" component={Review} />
                <PrivateRoute exact path="/review/:id" component={Review} />
                <PrivateRoute
                  exact
                  path="/profile-list"
                  component={ProfileList}
                />
                <PrivateRoute exact path="/offer" component={Offer} />
                <PrivateRoute
                  exact
                  path="/registration"
                  component={Registration}
                />
                <PrivateRoute
                  exact
                  path="/viewprofile/:id"
                  component={ViewProfile}
                />
                <PrivateRoute
                  exact
                  path="/registrationAdmin"
                  component={RegistrationAdmin}
                />
              </Switch>
            </div>
          </div>
          <footer class="text-muted">
            <div class="container-flex">
              <p>
                {this.state.organisation && this.state.organisation.system_name}, © 2020 |{" "}
                <a href={this.state.organisation && this.state.organisation.url}>
                {this.state.organisation && this.state.organisation.name}
                </a>{" "}
                |{" "}
                <a href="/PrivacyPolicy.pdf" target="_blank">
                  Privacy Policy
                </a>
                {this.state.organisation && this.state.organisation.system_name !== "Baobab" && 
                  <div class="float-right">
                    Powered by <a href="http://www.deeplearningindaba.com" target="_blank">Baobab</a>
                  </div>
                }
              </p>
            </div>
          </footer>
        </div>
      </Router>
    );
  }
}

export default App;
