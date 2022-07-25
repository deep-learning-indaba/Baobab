import React, { Component } from "react";
import "./Payment.css";

// TODO: Add translations once invoices have been translated.

export default class Payment extends Component {
    render() {
        return (
            <div>
                <h1>Payment Successful</h1>
                <p>Thank you for your payment. A receipt has been sent to your email address and your registration be confirmed soon.</p>
            </div>
        );
    }
}