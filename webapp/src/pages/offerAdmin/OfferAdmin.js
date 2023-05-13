import React, { Component } from "react";
import "./OfferAdmin.css";
import OfferAdminComponent from "./components/OfferAdminComponent.js";

export default class OfferAdmin extends Component {
    render() {
        return (
            <OfferAdminComponent
                {...this.props}>
            </OfferAdminComponent>
        );
    }
}