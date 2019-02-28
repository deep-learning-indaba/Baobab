import axios from "axios";
import { authHeader } from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export function getEvents() {
    return axios
        .get(baseUrl + `/api/v1/events`, { 'headers': authHeader() })
        .then(function (response) {
            // handle success
            return response.data;
        })
        .catch(function (error) {
            // handle error
            return { error: error };
        });
}
