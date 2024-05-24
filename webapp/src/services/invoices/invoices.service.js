import axios from "axios";
import { authHeader, extractErrorMessage } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const invoiceService = {
    getAllInvoices,
    getInvoice,
    initiatePayment,
    getAllInvoicesForEvent,
    cancelInvoice,
    markInvoicePaid
}

function getAllInvoices() {
    return axios
        .get(baseUrl + `/api/v1/invoice-list`, { headers: authHeader() })
        .then((response) => {
            return {
                invoices: response.data,
                error: ""
            }
        })
        .catch((error) => {
            return {
                invoices: null,
                error: extractErrorMessage(error)
            }
        });
}


function getInvoice(invoiceId) {
    return axios
        .get(baseUrl + `/api/v1/invoice?invoice_id=${invoiceId}`, { headers: authHeader() })
        .then((response) => {
            return {
                invoice: response.data,
                error: ""
            }
        })
        .catch((error) => {
            return {
                invoice: null,
                error: extractErrorMessage(error)
            }
        });
}

function initiatePayment(invoiceId) {
    const data = {
        invoice_id: invoiceId
    };

    return axios
        .post(baseUrl + "/api/v1/payment", data, { headers: authHeader() })
        .then((response) => {
            return {
                paymentInfo: response.data,
                error: ""
            }
        })
        .catch((error) => {
            return {
                paymentInfo: null,
                error: extractErrorMessage(error)
            }
        });
}

function getAllInvoicesForEvent(eventId) {
    return axios
        .get(baseUrl + `/api/v1/invoice-admin-list?event_id=${eventId}`, { headers: authHeader() })
        .then((response) => {
            return {
                invoices: response.data,
                error: ""
            }
        })
        .catch((error) => {
            return {
                invoices: null,
                error: extractErrorMessage(error)
            }
        });
}

function updateInvoice(invoiceId, eventId, action) {
    const data = {
        invoice_id: invoiceId,
        event_id: eventId,
        action: action
    };

    return axios
        .put(baseUrl + "/api/v1/invoice-admin", data, { headers: authHeader() })
        .then((response) => {
            return {
                updatedInvoice: response.data,
                error: ""
            }
        })
        .catch((error) => {
            return {
                updateInvoice: null,
                error: extractErrorMessage(error)
            }
        });

}

function cancelInvoice(invoiceId, eventId) {
    return updateInvoice(invoiceId, eventId, "cancel");
}

function markInvoicePaid(invoiceId, eventId) {
    return updateInvoice(invoiceId, eventId, "mark_as_paid");
}
