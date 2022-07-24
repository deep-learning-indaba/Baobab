import React, { Component } from "react";
import "./Payment.css";

// TODO: Add translations once invoices have been translated.

export default class Payment extends Component {
    render() {
        return (
            <div>
                <h1>Payment Failed</h1>
                <p>Unfortunately your payment was not processed succesfully. Please try again later.</p>
            </div>
        );
    }
}