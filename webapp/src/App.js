import React, { Component } from 'react';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';

import Home from './pages/home';
import './App.css';

class App extends Component {
  render() {
    return (
      <Router>
      <div className="App">
        <header className="App-header">
        <Link to="/">Home</Link>
        </header>
        <div className="Body">
            <Route exact path="/" component={Home} />
        </div>
      </div>
      </Router>
    );
  }
}

export default App;
