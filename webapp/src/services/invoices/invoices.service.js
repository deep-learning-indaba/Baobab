import axios from "axios";
import { authHeader, extractErrorMessage } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const invoiceService = {
    getAllInvoices,
    getInvoice,
    initiatePayment
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
