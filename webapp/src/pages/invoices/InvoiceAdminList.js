import React, { Component } from "react";
import "./Invoices.css";
import InvoiceAdminListComponent from "./components/InvoiceAdminListComponent";

export default class InvoiceAdminList extends Component {
    render() {
        return (
            <InvoiceAdminListComponent
                {...this.props}>
            </InvoiceAdminListComponent>
        );
    }
}