import axios from "axios";
import { authHeader, extractErrorMessage } from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const formConfigService = {
    getFormConfig,
    createTypedForm
}

function getFormConfig(eventId) {
    return axios.get(baseUrl + '/api/v1/form-config?event_id=' + eventId, {
        headers: authHeader()
    })
    .then(function(response) {
        return {
            config: response.data,
            error: "",
            statusCode: response.status
        };
    })
    .catch(function(error) {
        return {
            config: null,
            error: extractErrorMessage(error),
            statusCode: error.response && error.response.status
        };
    });
}

function createTypedForm(eventId, formType, stage) {
    var payload = {
        event_id: eventId,
        form_type: formType
    };
    if (stage !== undefined && stage !== null) {
        payload.stage = stage;
    }
    return axios.post(baseUrl + '/api/v1/forms', payload, {
        headers: authHeader()
    })
    .then(function(response) {
        return {
            form: response.data,
            error: "",
            statusCode: response.status
        };
    })
    .catch(function(error) {
        return {
            form: null,
            error: extractErrorMessage(error),
            statusCode: error.response && error.response.status
        };
    });
}
