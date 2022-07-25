import React, { Component } from "react";
import "./Invoices.css";
import InvoiceListComponent from "./components/InvoiceListComponent";

export default class InvoiceList extends Component {
    render() {
        return (
            <InvoiceListComponent
                {...this.props}>
            </InvoiceListComponent>
        );
    }
}