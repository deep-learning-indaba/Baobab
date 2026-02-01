import React, { Component } from "react";
import "./FormResponseDetail.css";
import FormResponseDetailComponent from "./components/FormResponseDetailComponent";

export default class FormResponseDetail extends Component {
  render() {
    return (
      <FormResponseDetailComponent
        {...this.props}
      />
    );
  }
}
