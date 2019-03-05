import React, { Component } from "react";
import "./VerifyEmail.css";
import VerifyEmailComponent from "./components/VerifyEmailComponent.js"

export default class VerifyEmail extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <VerifyEmailComponent></VerifyEmailComponent> 
    );
  }
}