import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const referenceService = {
    getReferenceRequests,
    requestReference
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

function requestReference(responseId, title, firstname, lastname, email, relation) {
    let data = {
        response_id: responseId,
        title: title,
        firstname: firstname,
        lastname: lastname,
        email: email,
        relation: relation
    };

    return axios
        .post(baseUrl + "/api/v1/reference-request", data, {
            headers: authHeader()
        })
        .then(function (response) {
            return {
                error: "",
                referenceRequest: response.data
            };
        })
        .catch(function (error) {
            return {
                error:
                    error.response && error.response.data && error.response.data.message
                        ? error.response.data.message
                        : error.message,
                referenceRequest: null
            };
        });
}