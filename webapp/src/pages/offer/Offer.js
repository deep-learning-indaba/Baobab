import React, { Component } from "react";
import "./Offer.css";
import OfferComponent from "./components/OfferComponent.js";

export default class Offer extends Component{
    constructor(props){
        super(props);
    }

    render(){
        return (
            <OfferComponent></OfferComponent>
        );
    }
}