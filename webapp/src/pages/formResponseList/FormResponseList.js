import React, { Component } from "react";
import "./FormResponseList.css";
import FormResponseListComponent from "./components/FormResponseListComponent";

export default class FormResponseList extends Component {
  render() {
    return (
      <FormResponseListComponent
        {...this.props}
      />
    );
  }
}
