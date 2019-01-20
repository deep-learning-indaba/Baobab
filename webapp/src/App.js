import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link, NavLink } from 'react-router-dom';
import logo from './images/logo-32x32-white.png'
import Home from './pages/home';
import Login from './pages/login';
import CreateAccount from './pages/createAccount'
import ApplicationForm from './pages/applicationForm'
import { PrivateRoute } from './components';
import './App.css';

class App extends Component {
  render() {
    return (
      <Router>
        <div>
          <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <a class="navbar-brand" href="/">
              <img src={logo} width="30" height="30" class="d-inline-block align-top" alt="" />
              Baobab
            </a>
            <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
              <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
              <ul class="navbar-nav">
                <li class="nav-item active">
                  <NavLink to="/" activeClassName="nav-link active" class="nav-link">Home <span class="sr-only">(current)</span></NavLink>
                </li>
                <li class="nav-item">
                  <NavLink to="/login" activeClassName="nav-link active" class="nav-link">Login</NavLink>
                </li>
                <li class="nav-item">
                  <NavLink to="/applicationForm" activeClassName="nav-link active" class="nav-link">Apply</NavLink>
                </li>
              </ul>
            </div>
          </nav>

          <div className="Body">
            <PrivateRoute exact path="/" component={Home} />
            <Route exact path="/login" component={Login} />
            <Route exact path="/createAccount" component={CreateAccount} />
            <Route exact path="/applicationForm" component={ApplicationForm} />
          </div>
        </div>
      </Router>
    );
  }
}

export default App;
