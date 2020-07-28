import React, { Component, Suspense } from "react";
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
import ViewFile from "./components/ViewFile";
import Reference from "./pages/references";
import CookieConsent from "react-cookie-consent";
import Loading from "./components/Loading";

import ReactGA from "react-ga";
import "./App.css";
import history from "./History";
import { organisationService } from "./services/organisation/organisation.service";
import { isEventAdmin, isRegistrationAdmin, isRegistrationVolunteer, isEventReviewer } from "./utils/user";
import { withTranslation } from 'react-i18next';
import { userService } from "./services/user";

ReactGA.initialize("UA-136093201-1", {
  debug: false,
  testMode: process.env.NODE_ENV === "test"
});

ReactGA.pageview(window.location.pathname + window.location.search);
history.listen(location => {
  ReactGA.pageview(location.pathname + location.search);
});


class EventNav extends Component {
  constructor(props) {
    super(props);

    this.state = {
      collapsed: true
    };
  }

  render() {
    const t = this.props.t;

    return (
      <nav class="navbar navbar-expand-sm bg-white navbar-light">
        <a href={`/${this.props.eventKey}`} class="navbar-brand">{this.props.event.name}</a>
        <div class={
          "collapse navbar-collapse" +
          (this.state.collapsed ? " collapsed" : "")
        } id="eventNavbar">
          <ul className="navbar-nav">
            {this.props.user &&
              this.props.event &&
              this.props.event.is_application_open && (
                <li className="nav-item">
                  <NavLink
                    to={`/${this.props.eventKey}/apply`}
                    activeClassName="nav-link active"
                    className="nav-link"
                    onClick={this.props.toggleMenu}
                  >
                    {t('Apply')}
                  </NavLink>
                </li>
              )}
            {this.props.user && this.props.event && this.props.event.is_offer_open && (
              <li className="nav-item">
                <NavLink
                  to={`/${this.props.eventKey}/offer`}
                  activeClassName="nav-link active"
                  className="nav-link"
                  onClick={this.props.toggleMenu}
                >
                  {t('Offer')}
                </NavLink>
              </li>
            )}
            {this.props.user &&
              this.props.event &&
              this.props.event.is_registration_open && (
                <li className="nav-item dropdown ">
                  <div
                    className="nav-link dropdown-toggle"
                    id="navbarDropdown"
                    role="button"
                    data-toggle="dropdown"
                    aria-haspopup="true"
                    aria-expanded="false"
                  >
                    {t('Registration')}
                  </div>
                  <div className="dropdown-menu" aria-labelledby="navbarDropdown">
                    <NavLink
                      to={`/${this.props.eventKey}/registration`}
                      className="dropdown-item"
                      onClick={this.props.toggleMenu}
                    >
                      {t('Registration Form')}
                    </NavLink>
                    {isRegistrationVolunteer(this.state.user) && (
                      <NavLink
                        to={`/${this.props.eventKey}/eventAttendance`}
                        className="dropdown-item"
                        onClick={this.props.toggleMenu}
                      >
                        {t('Event Attendance')}
                      </NavLink>
                    )}
                  </div>
                </li>
              )}
            {isEventAdmin(this.props.user, this.props.event) && (
              <li className="nav-item dropdown">
                <div
                  className="nav-link dropdown-toggle"
                  id="navbarDropdown"
                  role="button"
                  data-toggle="dropdown"
                  aria-haspopup="true"
                  aria-expanded="false"
                >
                  {t('Event Admin')}
                </div>
                <div className="dropdown-menu" aria-labelledby="navbarDropdown">
                  <NavLink
                    to={`/${this.props.eventKey}/reviewAssignment`}
                    className="dropdown-item"
                    onClick={this.props.toggleMenu}
                  >
                    {t('Review Assignment')}
                  </NavLink>
                  <NavLink
                    to={`/${this.props.eventKey}/invitedGuests`}
                    className="dropdown-item"
                    onClick={this.props.toggleMenu}
                  >
                    {t('Invited Guests')}
                  </NavLink>
                </div>
              </li>
            )}
            {isEventReviewer(this.props.user, this.props.event) &&
              this.props.event &&
              this.props.event.is_review_open && (
                <li className="nav-item dropdown">
                  <div
                    className="nav-link dropdown-toggle"
                    id="navbarDropdown"
                    role="button"
                    data-toggle="dropdown"
                    aria-haspopup="true"
                    aria-expanded="false"
                  >
                    {t('Reviews')}
                  </div>
                  <div className="dropdown-menu" aria-labelledby="navbarDropdown">
                    <NavLink
                      to={`/${this.props.eventKey}/review`}
                      className="dropdown-item"
                      onClick={this.props.toggleMenu}
                    >
                      {t('Review')}
                    </NavLink>
                    <NavLink
                      to={`/${this.props.eventKey}/reviewHistory`}
                      className="dropdown-item"
                      onClick={this.props.toggleMenu}
                    >
                      {t('Review History')}
                    </NavLink>
                  </div>
                </li>
              )}
            {isRegistrationAdmin(this.props.user, this.props.event) &&
              this.props.event &&
              this.props.event.is_registration_open && (
                <li className="nav-item dropdown">
                  <div
                    className="nav-link dropdown-toggle"
                    id="navbarDropdown"
                    role="button"
                    data-toggle="dropdown"
                    aria-haspopup="true"
                    aria-expanded="false"
                  >
                    {t('Registration Admin')}
                  </div>
                  <div className="dropdown-menu" aria-labelledby="navbarDropdown">
                    <NavLink
                      to={`/${this.props.eventKey}/registrationAdmin`}
                      className="dropdown-item"
                      onClick={this.props.toggleMenu}
                    >
                      {t('Unconfirmed Registrations')}
                    </NavLink>
                  </div>
                </li>
              )}
          </ul>
        </div>
        <button
          className="navbar-toggler"
          type="button"
          data-toggle="collapse"
          data-target="#eventNavbar"
          aria-controls="eventNavbar"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon" />
        </button>
      </nav>

    );
  }
}


const EventNavTranslation = withTranslation()(EventNav);


class LanguageSelectorComponent extends Component {
  changeLanguage = (lang) => {
    // Change the language using i18next
    if (this.props.i18n) {
      this.props.i18n.changeLanguage(lang).then(()=>{
        // We send a put request to the user service to update the language on the back-end. 
        // Note the language is automatically sent with every request through axios
        userService.get().then(result => {
          userService.update({
            email: result.email,
            firstName: result.firstname,
            lastName: result.lastName,
            title: result.user_title
          });
        })
      });
    }
  }

  render() {
    if (this.props.organisation && this.props.organisation.languages.length > 1) {
      return (
        <ul class="navbar-nav language-navbar">
          <li class="nav-item dropdown">
            <button
              class="nav-link dropdown-toggle link-style"
              id="userDropdown"
              data-toggle="dropdown"
              aria-haspopup="true"
              aria-expanded="false"
            >
              <i class="fas fa-globe menu-icon" />{" "}
              {this.props.i18n.language}
            </button>
            <div className="dropdown-menu" aria-labelledby="userDropdown">
              {this.props.organisation.languages.map(lang => (
                <button className="dropdown-item cursor-pointer" onClick={()=>this.changeLanguage(lang.code)} key={lang.code}>{lang.description}</button>
              ))}
            </div>
          </li>
        </ul>)
    }

    return <div></div>
  }
}

const LanguageSelector = withTranslation()(LanguageSelectorComponent);

class AppComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: {},
      organisation: null,
      collapsed: true,
      eventKey: null,
      currentEvent: null
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
      if (response.organisation) {
        document.title =
          response.organisation.system_name +
          " | " +
          response.organisation.name;
      }
    });
  }

  handleLogout = () => {
    this.refreshUser();
    window.location = '/';
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
      currentEvent: event
    });
  };

  render() {
    const t = this.props.t;

    return (
      <Router history={history}>
        <div>
          <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
            <a className="navbar-brand navbar-brand-main" href="/">
              <img
                src={
                  this.state.organisation &&
                  require("./images/" + this.state.organisation.icon_logo)
                }
                width="30"
                height="30"
                className="d-inline-block align-top brand-image"
                alt=""
              />
              {this.state.organisation && this.state.organisation.system_name}
            </a>
            <div
              class={
                "collapse navbar-collapse" +
                (this.state.collapsed ? " collapsed" : "")
              }
              id="navbarNav"
            >
              <ul className="navbar-nav mr-auto"></ul>
              <LanguageSelector organisation={this.state.organisation} />
              <UserDropdown
                logout={this.handleLogout}
                user={this.state.user}
                onClick={this.toggleMenu}
              />
            </div>
            <div>
              <ul className="navbar-nav mr-auto"></ul>
            </div>
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
          </nav>
          {this.state.currentEvent && <EventNavTranslation
            eventKey={this.state.eventKey}
            event={this.state.currentEvent}
            user={this.state.user} />}
          <div className="Body">
            <div className="container-fluid">
              <Switch>
                <Route
                  exact
                  path="/"
                  render={props => (
                    <Home
                      {...props}
                      user={this.state.user}
                      setEvent={this.setEvent}
                    />
                  )}
                />
                <Route
                  exact
                  path="/login"
                  render={props => (
                    <Login {...props} loggedIn={this.refreshUser} organisation={this.state.organisation} />
                  )}
                />
                <Route
                  exact
                  path="/createAccount"
                  render={props => (
                    <CreateAccount
                      {...props}
                      loggedIn={this.refreshUser}
                      organisation={this.state.organisation}
                    />
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
                <Route exact path="/file/:filename" component={ViewFile} />
                <PrivateRoute exact path="/profile" component={Profile} />
                <Route exact path="/reference/:token" component={Reference} />
                <Route
                  path="/:eventKey"
                  render={props => (
                    <EventHome {...props}
                      setEvent={this.setEvent}
                      user={this.state.user}
                      eventKey={this.state.eventKey}
                      event={this.state.currentEvent} />
                  )}
                />
              </Switch>
            </div>
          </div>
          <footer className="text-muted">
            <div className="container-flex">
              <div>
                {this.state.organisation && this.state.organisation.system_name}
                , © 2020 |{" "}
                <a
                  href={this.state.organisation && this.state.organisation.url}
                >
                  {this.state.organisation && this.state.organisation.name}
                </a>{" "}
                |{" "}
                <a
                  href={
                    "/" +
                    (this.state.organisation
                      ? this.state.organisation.privacy_policy
                      : "")
                  }
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {t('Privacy Policy')}
                </a>
                {this.state.organisation &&
                  this.state.organisation.system_name !== "Baobab" && (
                    <div className="float-right powered-by">
                      {t('Powered by')}{" "}
                      <a
                        href="http://www.deeplearningindaba.com"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Baobab
                      </a>
                    </div>
                  )}
              </div>
            </div>
          </footer>
          <CookieConsent
            cookieName="baobab-cookie-consent"
            style={{ background: "#343a40" }}
            buttonStyle={{ fontWeight: "bold" }}
            buttonText={t("I understand")}
            buttonClasses="btn btn-primary"
            buttonId="btn-cookieConsent"
            containerClasses="alert alert-warning col-lg-12"
          >
            <h5>{t('cookieTitle')}</h5>
            <span style={{ fontSize: "0.8em" }}>
              {t('cookieText')}
              <a
                href={
                  "/" +
                  (this.state.organisation
                    ? this.state.organisation.privacy_policy
                    : "")
                }
              >
                {t('Privacy Policy')}
              </a>
            </span>
          </CookieConsent>
        </div>
      </Router>
    );
  }
}

const AppTranslation = withTranslation()(AppComponent);

export default function App() {
  return <Suspense fallback={<Loading />}>
    <AppTranslation />
  </Suspense>
}
