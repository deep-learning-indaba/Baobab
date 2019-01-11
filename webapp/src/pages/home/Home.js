import React, { Component } from 'react';
import logo from '../../images/indaba-logo.png';
import './Home.css';

class Home extends Component {
  render() {
    return (
      <div >
          <img src={logo} className="Background" alt="logo" />
      </div>
    );
  }
}

export default Home;
