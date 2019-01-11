import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import { Navbar, Nav, NavItem } from 'react-bootstrap';

import Home from './pages/home';
import './App.css';

class App extends Component {
  render() {
    return (
      <Router>
        <div >
          <Navbar className="HomeNavBar" >
            <Nav>
              <NavItem eventKey={1} href="#">
                Home
              </NavItem>
            </Nav>
          </Navbar>
          <div className="Body">
            <Route exact path="/" component={Home} />
          </div>
        </div>
      </Router>
    );
  }
}

export default App;
