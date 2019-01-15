import React, { Component } from 'react';
import logo from '../../images/indaba-logo.png';
import './Home.css';

class Home extends Component {

  constructor(props) {
    super(props);

    this.state = {
        user: {},
    };
  }

  componentDidMount() {
    this.setState({ 
        user: JSON.parse(localStorage.getItem('user')),
    });
  }

  render() {
    return (
      <div >
          <img src={logo} className="Logo" alt="logo" />
          {this.state.user && <h3>Logged in as user id {this.state.user.id}</h3>}
      </div>
    );
  }
}

export default Home;
