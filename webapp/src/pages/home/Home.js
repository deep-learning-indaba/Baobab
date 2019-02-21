import React, { Component } from 'react';
import logo from '../../images/indaba-logo.png';
import './Home.css';

class Home extends Component {

  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div >
          <img src={logo} className="Logo" alt="logo" />
      </div>
    );
  }
}

export default Home;
