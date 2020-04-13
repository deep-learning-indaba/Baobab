import React, { Component } from "react";
import { NavLink } from "react-router-dom";
import { withRouter } from "react-router";
import { userService } from "../services/user";
import isEqual from "lodash.isequal";

class UserDropdown extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: props.user
    };
  }

  componentWillReceiveProps = props => {
    let userFromStorage = JSON.parse(localStorage.getItem("user"));
    if (!isEqual(userFromStorage, props.user)) {
      this.setState({ user: userFromStorage });
    } else this.setState({ user: props.user });
  };

  handleLogout = () => {
    this.props.onClick();
    userService.logout();
    if (this.props.logout) {
      this.props.logout();
    }
  };

  render() {
    if (this.state.user) {
      return (
        <ul class="navbar-nav">
          <li class="nav-item dropdown">
            <button
              class="nav-link dropdown-toggle link-style"
              id="userDropdown"
              data-toggle="dropdown"
              aria-haspopup="true"
              aria-expanded="false"
            >
              <i class="fas fa-user" />{" "}
              {this.state.user.firstname + " " + this.state.user.lastname}
            </button>
            <div class="dropdown-menu" aria-labelledby="userDropdown">
              <a
                className="dropdown-item"
                href="/profile"
                onClick={this.props.onClick}
              >
                Profile
              </a>
              <button className="dropdown-item nav-link" onClick={this.handleLogout}>
                Logout
              </button>
            </div>
          </li>
        </ul>
      );
    } else {
      return (
        <ul class="navbar-nav">
          <li class="nav-item">
            <NavLink
              to="/login"
              activeClassName="nav-link active"
              className="nav-link"
              onClick={this.props.onClick}
            >
              Login
            </NavLink>
          </li>
        </ul>
      );
    }
  }
}

export default withRouter(UserDropdown);
