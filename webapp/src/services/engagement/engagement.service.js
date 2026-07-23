import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const engagementService = {
    logInstall,
}

function logInstall(eventId) {
    return axios
        .post(baseUrl + "/api/v1/engagement/install", { event_id: eventId }, { headers: authHeader() })
        .then(function(response) {
            return { ok: true };
        })
        .catch(function(error) {
            // Best-effort analytics — never surface this to the user.
            return { ok: false };
        });
}
