import React, { Component } from "react";
import "./Reference.css";
import ReferenceComponent from "./components/ReferenceComponent.js";

export default class Reference extends Component {

    render() {
        return (
            <ReferenceComponent
                {...this.props}>
            </ReferenceComponent>
        );
    }

}