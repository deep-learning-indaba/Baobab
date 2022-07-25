import React, { Component } from "react";
import { withRouter } from "react-router";
import { NavLink } from "react-router-dom";
import Loading from "../../../components/Loading";
import { invoiceService } from "../../../services/invoices/invoices.service";
import { Trans, withTranslation } from 'react-i18next'

/*
For now, list invoices with their totals, have a button to generate a PDF of the invoice, 
have a button to pay which takes to payment page.
Send an email when an invoice is created with the PDF and link to payment.
*/

class InvoiceList extends Component {
    constructor(props) {
        super(props);

        this.state = {
            loading: true,
            invoices: null,
            error: ""
        };

    }

    componentDidMount() {
        invoiceService.getAllInvoices()
            .then(response => {
                this.setState({
                    invoices: response.invoices,
                    error: response.error,
                    isLoading: false
                })
            });
    }

    render() {
        const { error, isLoading, invoices } = this.state;
        const t = this.props.t;
        
        if (isLoading) { return <Loading />; }

        if (error) {
            return (
                <div className={"alert alert-danger alert-container"}>
                    {JSON.stringify(error)}
                </div>
            );
        }

        return <div>
            <h1>{t("Invoices")}</h1>
            {JSON.stringify(invoices)}
        </div>;
    }
}

export default withRouter(withTranslation()(InvoiceList));