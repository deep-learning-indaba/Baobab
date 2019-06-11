import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const eventStatsService = {
    getStats,
    sendReminderToBegin,
    sendReminderToSubmit
}

function getStats(eventId) {
    return axios
        .get(baseUrl + "/api/v1/eventstats?event_id=" + eventId, { headers: authHeader() })
        .then(function(response) {
            return {
                stats: response.data,
                error: ""
            };
        })
        .catch(function(error) {
            return {
                stats: null,
                error: (error.response && error.response.data) ? error.response.data.message : error.message
            }
        });
}

function sendReminderToSubmit(eventId) {
    let event = {
        "event_id": eventId,
    };
    return axios
        .post(baseUrl + "/api/v1/reminder-unsubmitted", event, { headers: authHeader() })
        .then(function(response) {
            return {
                msg: "Reminders sent",
                error: ""
            }
        })
        .catch(function(error) {
            return {
                msg: "",
                error: (error.response && error.response.data) ? error.response.data.message : error.message
            }
        })
}

function sendReminderToBegin(eventId) {
    let event = {
        "event_id": eventId,
    };
    return axios
        .post(baseUrl + "/api/v1/reminder-not-started", event, { headers: authHeader() })
        .then(function(response) {
            return {
                msg: "Reminders sent",
                error: ""
            }
        })
        .catch(function(error) {
            return {
                msg: "Failed",
                error: (error.response && error.response.data) ? error.response.data.message : error.message
            }
        })
}


