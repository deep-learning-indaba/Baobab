import React, { Component } from "react";
import { NavLink } from "react-router-dom";
import { withRouter } from "react-router";
import { userService } from "../services/user";
import isEqual from "lodash.isequal";
import { withTranslation } from 'react-i18next';

class UserDropdown extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: props.user,
      isOpen: false
    };
    this.dropdownRef = React.createRef();
  }

  componentDidMount() {
    document.addEventListener("mousedown", this.handleClickOutside);
  }

  componentWillUnmount() {
    document.removeEventListener("mousedown", this.handleClickOutside);
  }

  handleClickOutside = (event) => {
    if (this.dropdownRef.current && !this.dropdownRef.current.contains(event.target)) {
      this.setState({ isOpen: false });
    }
  };

  componentWillReceiveProps = props => {
    let userFromStorage = JSON.parse(localStorage.getItem("user"));
    if (!isEqual(userFromStorage, props.user)) {
      this.setState({ user: userFromStorage });
    } else this.setState({ user: props.user });
  };

  handleLogout = () => {
    this.setState({ isOpen: false });
    this.props.onClick();
    userService.logout();
    if (this.props.logout) {
      this.props.logout();
    }
  };

  toggleDropdown = () => {
    this.setState(prevState => ({ isOpen: !prevState.isOpen }));
  };

  render() {
    const t = this.props.t;

    if (this.state.user) {
      return (
        <div className="relative inline-block text-left" ref={this.dropdownRef}>
          <button
            type="button"
            onClick={this.toggleDropdown}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-white hover:text-white/80 focus:outline-none transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center border border-white/20">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            </div>
            <span>{this.state.user.firstname} {this.state.user.lastname}</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9l6 6 6-6"/></svg>
          </button>

          {this.state.isOpen && (
            <div className="absolute right-0 mt-2 w-48 rounded-xl shadow-lg bg-white border border-border py-1 z-50 origin-top-right">
              <a
                href="/profile"
                className="block px-4 py-2 text-sm text-foreground hover:bg-surface-low transition-colors"
                onClick={(e) => {
                  this.setState({ isOpen: false });
                  this.props.onClick(e);
                }}
              >
                {t("Profile")}
              </a>
              <div className="h-px bg-border/50 my-1"></div>
              <button
                onClick={this.handleLogout}
                className="block w-full text-left px-4 py-2 text-sm text-error hover:bg-error/10 transition-colors"
              >
                {t("Sign Out")}
              </button>
            </div>
          )}
        </div>
      );
    } else {
      return (
        <div className="flex items-center">
          <NavLink
            to="/login"
            className="text-sm font-semibold text-white bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg transition-colors border border-white/20"
            onClick={this.props.onClick}
          >
            {t("Sign In")}
          </NavLink>
        </div>
      );
    }
  }
}

export default withRouter(withTranslation()(UserDropdown));
