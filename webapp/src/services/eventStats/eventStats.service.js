import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const eventStatsService = {
    getStats
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



