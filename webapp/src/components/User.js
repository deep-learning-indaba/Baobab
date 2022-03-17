import React, { Component } from "react";
import { NavLink } from "react-router-dom";
import { withRouter } from "react-router";
import { userService } from "../services/user";
import isEqual from "lodash.isequal";
import { withTranslation } from "react-i18next";

class UserDropdown extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: props.user,
    };
  }

  componentWillReceiveProps = (props) => {
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
    const t = this.props.t;

    if (this.state.user) {
      return (
        <ul className="navbar-nav">
          <li className="nav-item dropdown">
            <button
              className="nav-link dropdown-toggle link-style"
              id="userDropdown"
              data-toggle="dropdown"
              aria-haspopup="true"
              aria-expanded="false"
            >
              <i className="fas fa-user menu-icon" />{" "}
              {this.state.user.firstname + " " + this.state.user.lastname}
            </button>
            <div className="dropdown-menu" aria-labelledby="userDropdown">
              <a
                className="dropdown-item"
                href="/profile"
                onClick={this.props.onClick}
              >
                {t("Profile")}
              </a>
              <button
                className="dropdown-item cursor-pointer"
                onClick={this.handleLogout}
              >
                {t("Sign Out")}
              </button>
            </div>
          </li>
        </ul>
      );
    } else {
      return (
        <ul className="navbar-nav">
          <li className="nav-item">
            <NavLink
              to="/login"
              activeClassName="nav-link active"
              className="nav-link"
              onClick={this.props.onClick}
            >
              {t("Sign In")}
            </NavLink>
          </li>
        </ul>
      );
    }
  }
}

export default withRouter(withTranslation()(UserDropdown));
