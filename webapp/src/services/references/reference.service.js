import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const referenceService = {
    getReferenceRequests
}

function getReferenceRequests(responseId) {
    return axios
        .get(
            baseUrl +
            `/api/v1/reference-request/list?response_id=${responseId}`,
            {
                headers: authHeader()
            }
        )
        .then(function (response) {
            return {
                requests: response.data,
                error: ""
            };
        })
        .catch(function (error) {
            return {
                requests: null,
                error:
                    error.response && error.response.data
                        ? error.response.data.message
                        : error.message,
                statusCode: error.response && error.response.status
            };
        });
}