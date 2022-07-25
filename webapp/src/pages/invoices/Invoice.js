import React, { Component } from "react";
import "./Invoices.css";
import InvoiceComponent from "./components/InvoiceComponent";

export default class Invoice extends Component {
    render() {
        return (
            <InvoiceComponent
                {...this.props}>
            </InvoiceComponent>
        );
    }
}