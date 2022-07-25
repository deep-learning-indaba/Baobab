import React, { Component } from "react";
import "./Payment.css";
import PaymentComponent from "./components/PaymentComponent";

export default class Payment extends Component {
    render() {
        return (
            <PaymentComponent
                {...this.props}>
            </PaymentComponent>
        );
    }
}