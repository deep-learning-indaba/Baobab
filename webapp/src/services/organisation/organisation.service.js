import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const organisationService = {
    getOrganisation,
    getSettings,
    updateSettings
}

function getOrganisation() {
    return axios.get(baseUrl + "/api/v1/organisation")
        .then(function (response) {
            return {
                organisation: response.data,
                error: "",
                statusCode: response.status
            };
        })
        .catch(function (error) {
            return {
                organisation: null,
                error:
                    error.response && error.response.data
                        ? error.response.data.message
                        : error.message,
                statusCode: error.response && error.response.status
            };
        });
}


function settingsResult(promise) {
    return promise
        .then(function (response) {
            return { settings: response.data, error: "", field: null };
        })
        .catch(function (error) {
            const data = error.response && error.response.data;
            return {
                settings: null,
                error: data && data.message ? data.message : error.message,
                field: (data && data.field) || null,
                statusCode: error.response && error.response.status
            };
        });
}

function getSettings() {
    return settingsResult(
        axios.get(baseUrl + "/api/v1/organisation/settings", { headers: authHeader() }));
}

// Only the keys present in `changes` are updated on the server.
function updateSettings(changes) {
    return settingsResult(
        axios.put(baseUrl + "/api/v1/organisation/settings", changes, { headers: authHeader() }));
}
