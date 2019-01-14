import React, { Component } from "react";
import { userService } from '../../services/user';
import "./CreateAccount.css";
import CreateAccountForm from "./components/CreateAccountForm";

export default class CreateAccount extends Component {
  
    render() {
      return (
       <CreateAccountForm></CreateAccountForm> 
      );
    }
  }