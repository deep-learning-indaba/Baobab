import React, { Component } from "react";
import { Router, Route, Link, NavLink, Switch } from "react-router-dom";
import logo from "./images/logo-32x32-white.png";
import Home from "./pages/home";
import Login from "./pages/login";
import ResetPassword from "./pages/resetPassword";
import CreateAccount from "./pages/createAccount";
import Application from "./pages/applicationForm";
import VerifyEmail from "./pages/verifyEmail";
import Profile from "./pages/profile";
import { PrivateRoute } from "./components";
import UserDropdown from "./components/User";
import ReactGA from "react-ga";
import createHistory from "history/createBrowserHistory";
import "./App.css";

const history = createHistory();
ReactGA.initialize("UA-136093201-1", {
  debug: true,
  testMode: process.env.NODE_ENV === "test"
});

ReactGA.pageview(window.location.pathname + window.location.search);
history.listen((location, action) => {
  ReactGA.pageview(location.pathname + location.search);
});

class App extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: {},
      collapsed: true
    };

    this.refreshUser = this.refreshUser.bind(this);
  }

  componentDidMount() {
    this.setState({
      user: JSON.parse(localStorage.getItem("user"))
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

  render() {
    return (
      <Router history={history}>
        <div>
          <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <a class="navbar-brand" href="/">
              <img
                src={logo}
                width="30"
                height="30"
                class="d-inline-block align-top"
                alt=""
              />
              Baobab
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
                <PrivateRoute exact path="/profile" component={Profile} />} />
                <PrivateRoute
                  exact
                  path="/applicationForm"
                  component={Application}
                />
              </Switch>
            </div>
          </div>
          <footer class="text-muted">
            <div class="container">
              <p>
                Baobab, © 2019 |{" "}
                <a href="http://www.deeplearningindaba.com">
                  Deep Learning Indaba
                </a>
              </p>
            </div>
          </footer>
        </div>
      </Router>
    );
  }
}

export default App;
