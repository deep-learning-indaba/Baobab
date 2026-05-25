import React, { Component } from "react";
import { getImage } from "./utils/images";
import { Router, Route, NavLink, Switch } from "react-router-dom";
import Home from "./pages/home";
import EventHome from "./pages/eventHome";
import Login from "./pages/login";
import ResetPassword from "./pages/resetPassword";
import CreateAccount from "./pages/createAccount";
import EventConfig from "./pages/eventConfig";
import TagConfig from "./pages/tagConfig";
import VerifyEmail from "./pages/verifyEmail";
import Profile from "./pages/profile";
import { PrivateRoute } from "./components";
import UserDropdown from "./components/User";
import ViewFile from "./components/ViewFile";
import Reference from "./pages/references";
import CookieConsent from "react-cookie-consent";
import ResponseList from './pages/ResponseList/ResponseList';
import { AdminMenu } from './utils/adminMenu';
import { Payment, Success, Failed } from './pages/payment';

import ReactGA from "react-ga";
import "./App.css";
import history from "./History";

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


class LanguageSelectorComponent extends Component {
  constructor(props) {
    super(props);
    this.state = { isOpen: false };
    this.dropdownRef = React.createRef();
  }

  componentDidMount() {
    document.addEventListener("mousedown", this.handleClickOutside);
  }

  componentWillUnmount() {
    document.removeEventListener("mousedown", this.handleClickOutside);
  }

  handleClickOutside = (event) => {
    if (this.dropdownRef.current && !this.dropdownRef.current.contains(event.target)) {
      this.setState({ isOpen: false });
    }
  };

  changeLanguage = (lang) => {
    this.setState({ isOpen: false });
    if (this.props.i18n) {
      this.props.i18n.changeLanguage(lang).then(() => {
        const currentUser = JSON.parse(localStorage.getItem("user"))
        if (currentUser) {
          userService.get().then(result => {
            userService.update({
              email: result.email,
              firstName: result.firstname,
              lastName: result.lastname,
              title: result.user_title
            });
          });
        }
        window.location.reload(true);
      });
    }
  }

  render() {
    if (this.props.organisation && this.props.organisation.languages.length > 1) {
      return (
        <ul className="navbar-nav language-navbar" ref={this.dropdownRef}>
          <li className="nav-item dropdown">
            <button
              className="nav-link link-style"
              onClick={() => this.setState(s => ({ isOpen: !s.isOpen }))}
              aria-haspopup="true"
              aria-expanded={this.state.isOpen}
            >
              <i className="fas fa-globe menu-icon" />{" "}
              {this.props.i18n.language}
            </button>
            {this.state.isOpen && (
              <div className="dropdown-menu show" aria-labelledby="userDropdown">
                {this.props.organisation.languages.map(lang => (
                  <button className="dropdown-item cursor-pointer" onClick={() => this.changeLanguage(lang.code)} key={lang.code}>{lang.description}</button>
                ))}
              </div>
            )}
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
      user: JSON.parse(localStorage.getItem("user")),
      collapsed: true,
      eventKey: null,
      currentEvent: null,
      error: null
    };

    this.refreshUser = this.refreshUser.bind(this);
  }

  isAbsoluteUrl = (url) => {
    try {
      new URL(url);
      return true; // if it parses, it's a full URL
    } catch {
      return false; // invalid → treat as relative
    }
  };

  componentDidMount() {
    userService.authRefresh().then(user => {
      if (!user.error) {
        localStorage.setItem("user", JSON.stringify(user));
        this.setState({
          user: user
        });
      }
      else {
        localStorage.removeItem("user");
      }
    });
  }

  handleLogout = () => {
    this.refreshUser();
    window.location = '/';
  }

  refreshUser() {
    const currentUser = JSON.parse(localStorage.getItem("user"));
    this.setState({
      user: currentUser
    });

    if (currentUser) {
      // Send a user profile update to record the currently selected language
      userService.get().then(result => {
        userService.update({
          email: result.email,
          firstName: result.firstname,
          lastName: result.lastname,
          title: result.user_title
        });
      });
    }

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
        <div className="notranslate" translate="no">
          <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
            <a
              className={
                "navbar-brand navbar-brand-main" +
                (this.props.organisation && this.props.organisation.name !== "MenaML" ? " uppercase" : "")
              }
              href="/"
            >
              <img
                src={
                  this.props.organisation &&
                  getImage(this.props.organisation.icon_logo)
                }
                width="30"
                height="30"
                className="d-inline-block align-top brand-image"
                alt=""
              />
              {this.props.organisation && this.props.organisation.system_name}
            </a>
            <div
              className={
                "collapse navbar-collapse" +
                (this.state.collapsed ? " collapsed" : "")
              }
              id="navbarNav"
            >
              <ul className="navbar-nav mr-auto"></ul>
              <LanguageSelector organisation={this.props.organisation} />
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
              onClick={this.toggleMenu}
              aria-controls="navbarNav"
              aria-expanded={!this.state.collapsed}
              aria-label="Toggle navigation"
            >
              <span className="navbar-toggler-icon" />
            </button>
          </nav>
          <div className="Body">
            <div className="container-fluid">
              {this.state.error && <div className="alert alert-danger">{this.state.error}</div>}
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
                    <Login {...props} loggedIn={this.refreshUser} organisation={this.props.organisation} />
                  )}
                />
                <Route
                  exact
                  path="/createAccount"
                  render={props => (
                    <CreateAccount
                      {...props}
                      loggedIn={this.refreshUser}
                      organisation={this.props.organisation}
                    />
                  )}
                />
                <Route
                  exact
                  path="/eventConfig"
                  render={props => (
                    <EventConfig
                      {...props}
                      loggedIn={this.refreshUser}
                      organisation={this.props.organisation}
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
                <Route
                  exact
                  path="/responseList"
                  render={props => (
                    <ResponseList {...props} loggedIn={this.refreshUser} />
                  )}
                />
                <Route
                  exact
                  path="/tagConfig"
                  render={props => (
                    <TagConfig
                      {...props}
                      loggedIn={this.refreshUser}
                      organisation={this.props.organisation}
                    />
                  )}
                />
                <Route exact path="/verifyEmail" component={VerifyEmail} />
                <Route exact path="/file/:filename" component={ViewFile} />
                <PrivateRoute exact path="/profile" component={Profile} />
                <Route exact path="/reference/:token" component={Reference} />
                <PrivateRoute exact path="/payment/:invoiceId" component={Payment} />
                <Route exact path="/payment-success" component={Success} />
                <Route exact path="/payment-cancel" component={Failed} />

                <Route
                  path="/:eventKey"
                  render={props => (
                    <EventHome {...props}
                      setEvent={this.setEvent}
                      user={this.state.user}
                      eventKey={this.state.eventKey}
                      event={this.state.currentEvent}
                      organisation={this.props.organisation}
                    />
                  )}
                />
              </Switch>
            </div>
          </div>
          <footer className="text-muted">
            <div className="container-flex">
              <div>
                {this.props.organisation && this.props.organisation.system_name}
                , © {new Date().getFullYear()} |{" "}
                <a
                  href={this.props.organisation && this.props.organisation.url}
                >
                  {this.props.organisation && this.props.organisation.name}
                </a>{" "}
                |{" "}
                <a
                  href={
                    this.isAbsoluteUrl((this.props.organisation ? this.props.organisation.privacy_policy : ""))
                      ? this.props.organisation && this.props.organisation.privacy_policy
                      : "/" + ((this.props.organisation && this.props.organisation.privacy_policy) || "")
                  }
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {t('Privacy Policy')}
                </a>
                {this.props.organisation &&
                  this.props.organisation.system_name !== "Baobab" && (
                    <div className="float-right powered-by">
                      {t('Powered by')}{" "}
                      <a
                        href="https://www.deeplearningindaba.com"
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
              {t('cookieText')}{" "}
              <a
                href={
                  "/" +
                  (this.props.organisation
                    ? this.props.organisation.privacy_policy
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

const App = withTranslation()(AppComponent);

export default App;
