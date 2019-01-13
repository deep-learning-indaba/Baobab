import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import logo from './images/logo-32x32-white.png'
import Home from './pages/home';
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
                  <a class="nav-link" href="/">Home <span class="sr-only">(current)</span></a>
                </li>
              </ul>
            </div>
          </nav>

          <div className="Body">
            <Route exact path="/" component={Home} />
          </div>
        </div>
      </Router>
    );
  }
}

export default App;
