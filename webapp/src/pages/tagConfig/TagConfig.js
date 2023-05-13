import React, { Component } from "react";
import "./TagConfig.css";
import TagConfigComponent from "./components/TagConfigComponent.js";

export default class TagConfig extends Component {
  render() {
    return (
      <TagConfigComponent
        {...this.props}>
    </TagConfigComponent>
    );
  }
}
