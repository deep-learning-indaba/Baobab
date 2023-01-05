import React, { Component } from "react";
import "./Onboarding.css";
import OnboardingComponent from "./components/OnboardingComponent.js"

export default class Onboarding extends Component {

  render() {
    return (
      <OnboardingComponent
        {...this.props}>
      </OnboardingComponent>
    );
  }
}