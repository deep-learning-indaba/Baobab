import React, { Component } from "react";
import "./Offer.css";
import OfferComponent from "./components/OfferComponent.js";

export default class Offer extends Component{

    render(){
        return (
            <OfferComponent {...this.props}></OfferComponent>
        );
    }
}