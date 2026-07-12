import React, { Component } from "react";
import { withRouter } from "react-router";
import { invoiceService } from "../../../services/invoices/invoices.service";
import { Trans, withTranslation } from 'react-i18next'
import ReactTable from "react-table";
import { getDownloadURL } from "../../../utils/files";
import { ConfirmModal } from "../../../components/Modal";

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

        let badgeClass = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-warning/10 text-warning-text border border-warning-border/50";
        
        if (status === 'paid') {
            badgeClass = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-50 text-green-700 border border-green-200/50";
        }
        else if (props.original.is_overdue) {
            badgeClass = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-error/10 text-error border border-error/20";
            status = 'overdue';
        }
        else if (status === 'canceled') {
            badgeClass = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-error/10 text-error border border-error/20";
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
            <div className="action-buttons flex gap-2">
                {props.original.current_payment_status !== 'paid' && <button
                    className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50 cursor-pointer"
                    onClick={() => {
                    this.onMarkPaid(props.original);
                    }}
                    disabled={this.state.isActionProcessing}
                >
                    {t("Mark Paid")}
                </button>}
                {props.original.current_payment_status !== 'paid' && <button
                    className="inline-flex items-center justify-center p-1.5 rounded-lg text-sm font-semibold transition-colors bg-error/10 text-error hover:bg-error/20 border border-error/20 cursor-pointer"
                    onClick={() => {
                    this.onCancel(props.original);
                    }}
                    disabled={this.state.isActionProcessing}
                >
                    <i className="far fa-trash-alt"></i>
                </button>}
            </div>
        );
    }

    render() {
        const { error, isLoading, invoices, selectedInvoice } = this.state;
        const t = this.props.t;
        const selectedInvoiceNumber = selectedInvoice ? selectedInvoice.invoice_number : "";
        
        if (isLoading) {
            return (
                <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            );
        }

        if (error) {
            return (
                <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
                    {JSON.stringify(error)}
                </div>
            );
        }

        const columns = [
            {
                id: 'number',
                Header: <div className="text-left font-bold">{t("Invoice Number")}</div>,
                accessor: 'invoice_number',
                Cell: props => <a href={getDownloadURL(`invoice_${props.value}`, "indaba-invoices")} className="text-primary hover:underline font-semibold">
                    {props.value}
                </a>
            },
            {
                id: 'email',
                Header: <div className="text-left font-bold">{t("Email")}</div>,
                accessor: 'customer_email'
            },
            {
                id: 'name',
                Header: <div className="text-left font-bold">{t("Name")}</div>,
                accessor: 'customer_name',
                Cell: props => <span className="font-medium text-foreground">{props.value}</span>
            },
            {
                id: 'due_date',
                Header: <div className="text-left font-bold">{t("Due Date")}</div>,
                accessor: 'due_date'
            },
            {
                id: 'currency',
                Header: <div className="text-left font-bold">{t("Currency")}</div>,
                accessor: 'iso_currency_code'
            },
            {
                id: 'amount',
                Header: <div className="text-left font-bold">{t("Amount")}</div>,
                accessor: 'total_amount'
            },
            {
                id: 'status',
                Header: <div className="text-left font-bold">{t("Status")}</div>,
                accessor: 'current_payment_status',
                Cell: this.invoiceStatusCell
            },
            {
                id: 'actions',
                Header: <div className="text-left font-bold">{t("Action")}</div>,
                accessor: 'id',
                Cell: this.actionCell
            }
        ];

        return (
            <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-6">
                <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6">
                    <h1 className="font-heading text-2xl font-bold text-foreground mb-6">{t("Invoice Admin")}</h1>
                    <div className="react-table">
                        <ReactTable
                            data={invoices}
                            columns={columns}
                            minRows={0}
                            className="ReactTable"
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