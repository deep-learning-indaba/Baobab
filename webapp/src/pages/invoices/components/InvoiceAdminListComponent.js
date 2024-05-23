import React, { Component } from "react";
import { withRouter } from "react-router";
import { NavLink } from "react-router-dom";
import Loading from "../../../components/Loading";
import { invoiceService } from "../../../services/invoices/invoices.service";
import { Trans, withTranslation } from 'react-i18next'
import ReactTable from "react-table";
import { getDownloadURL } from "../../../utils/files";
import { ConfirmModal } from "react-bootstrap4-modal";

class InvoiceAdminList extends Component {
    constructor(props) {
        super(props);

        this.state = {
            loading: true,
            invoices: [],
            error: "",
            isActionProcessing: false,
            selectedInvoice: null
        };

    }

    componentDidMount() {
        invoiceService.getAllInvoicesForEvent(this.props.event.id)
            .then(response => {
                this.setState({
                    invoices: response.invoices,
                    error: response.error,
                    isLoading: false
                })
            });
    }

    invoiceStatusCell = (props) => {
        let status = props.value;
        const t = this.props.t;

        let badgeClass = "badge badge-warning";
        
        if (status === 'paid') {
            badgeClass = "badge badge-success";
        }
        else if (props.original.is_overdue) {
            badgeClass = "badge badge-danger";
            status = 'overdue';
        }
        else if (status === 'canceled') {
            badgeClass = "badge badge-danger";
        }

        return <span className={badgeClass}>{t(status)}</span>;
    }

    onMarkPaid = (invoice) => {
        this.setState({ 
            selectedInvoice: invoice, 
            confirmMarkPaidVisible: true 
        });
    }

    confirmMarkPaid = () => {
        this.setState({ isActionProcessing: true });
        invoiceService.markInvoicePaid(this.state.selectedInvoice.id, this.props.event.id)
            .then(response => {
                this.setState({
                    isActionProcessing: false,
                    confirmMarkPaidVisible: false,
                    error: response.error,
                    invoices: this.state.invoices.map(invoice => {
                        if (response.updatedInvoice && invoice.id === response.updatedInvoice.id) {
                            return response.updatedInvoice;
                        }
                        return invoice;
                    })
                });
            });
    }

    onCancel = (invoice) => {
        this.setState({
            selectedInvoice: invoice,
            confirmCancelVisible: true
        });
    }

    confirmCancel = () => {
        this.setState({ isActionProcessing: true });
        invoiceService.cancelInvoice(this.state.selectedInvoice.id, this.props.event.id)
            .then(response => {
                this.setState({
                    isActionProcessing: false,
                    confirmCancelVisible: false,
                    error: response.error,
                    invoices: this.state.invoices.filter(invoice => {
                        return !response.updatedInvoice || (invoice.id !== response.updatedInvoice.id)
                    })
                });
            });
    }   

    actionCell = (props) => {
        const t = this.props.t;
        return (
            <div className="action-buttons">
                {props.original.current_payment_status !== 'paid' && <button
                    className="btn btn-primary btn-sm"
                    onClick={() => {
                    this.onMarkPaid(props.original);
                    }}
                    disabled={this.state.isActionProcessing}
                >
                    {t("Mark Paid")}
                </button>}
                {props.original.current_payment_status !== 'paid' && <button
                    className="text-danger button-trash"
                    onClick={() => {
                    this.onCancel(props.original);
                    }}
                    disabled={this.state.isActionProcessing}
                >
                    <i class="far fa-trash-alt"></i>
                </button>}
            </div>
        );
    }

    render() {
        const { error, isLoading, invoices, selectedInvoice } = this.state;
        const t = this.props.t;
        const selectedInvoiceNumber = selectedInvoice ? selectedInvoice.invoice_number : "";
        
        if (isLoading) { return <Loading />; }

        if (error) {
            return (
                <div className={"alert alert-danger alert-container"}>
                    {JSON.stringify(error)}
                </div>
            );
        }

        const columns = [
            {
                id: 'number',
                Header: t("Invoice Number"),
                accessor: 'invoice_number',
                Cell: props => <a href={getDownloadURL(`invoice_${props.value}`, "indaba-invoices")}>
                    {props.value}
                </a>
            },
            {
                id: 'email',
                Header: t("Email"),
                accessor: 'customer_email'
            },
            {
                id: 'name',
                Header: t("Name"),
                accessor: 'customer_name'
            },
            {
                id: 'due_date',
                Header: t("Due Date"),
                accessor: 'due_date'
            },
            {
                id: 'currency',
                Header: t("Currency"),
                accessor: 'iso_currency_code'
            },
            {
                id: 'amount',
                Header: t("Amount"),
                accessor: 'total_amount'
            },
            {
                id: 'status',
                Header: t("Status"),
                accessor: 'current_payment_status',
                Cell: this.invoiceStatusCell
            },
            {
                id: 'actions',
                Header: t("Action"),
                accessor: 'id',
                Cell: this.actionCell
            }
        ];

        return (<div className="invoice-admin-list-container">
            <h2 className="title">
                {t("Invoice Admin")}
            </h2>

            <div className="card">
                <div className="card-body">
                    <h3 className="card-title">{t("Invoices")}</h3>
                    <ReactTable
                        data={invoices}
                        columns={columns}
                        minRows={0}
                    />
                </div>
            </div>

            <ConfirmModal
                visible={this.state.confirmMarkPaidVisible}
                onOK={this.confirmMarkPaid}
                onCancel={() => this.setState({ confirmMarkPaidVisible: false })}
                okText={t("Yes")}
                cancelText={t("No")}>
                <p>
                    <Trans key="confirmInvoicePaid">Are you sure you want to mark invoice {{selectedInvoiceNumber}} as paid?</Trans>
                </p>
            </ConfirmModal>

            <ConfirmModal
                visible={this.state.confirmCancelVisible}
                onOK={this.confirmCancel}
                onCancel={() => this.setState({ confirmCancelVisible: false })}
                okText={t("Yes")}
                cancelText={t("No")}>
                <p>
                    <Trans key="confirmInvoiceCancel">Are you sure you want cancel invoice {{selectedInvoiceNumber}}?</Trans>
                </p>
            </ConfirmModal>

        </div>);
    }
}

export default withRouter(withTranslation()(InvoiceAdminList));