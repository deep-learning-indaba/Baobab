import axios from "axios";
import { authHeader, extractErrorMessage } from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const formServices = {
    getFormList,
    getForm,
    createForm,
    updateForm,
    deleteForm,
    getFormStructure,
    updateFormStructure
}

function getFormList(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.language) params.append('language', filters.language);
    if (filters.is_active !== undefined) params.append('is_active', filters.is_active);
    if (filters.is_open !== undefined) params.append('is_open', filters.is_open);
    if (filters.created_by) params.append('created_by', filters.created_by);
    
    const queryString = params.toString() ? `?${params.toString()}` : '';
    
    return axios.get(baseUrl + "/api/v1/forms" + queryString, {
        headers: authHeader()
    })
    .then(function(response) {
        return {
            forms: response.data,
            error: "",
            statusCode: response.status
        };
    })
    .catch(function(error) {
        return {
            forms: null,
            error: extractErrorMessage(error),
            statusCode: error.response && error.response.status
        };
    });
}

function getForm(formId, language = 'en') {
    return axios.get(baseUrl + `/api/v1/forms/${formId}?language=${language}`, {
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

function createForm(formData) {
    return axios.post(baseUrl + "/api/v1/forms", formData, {
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

function updateForm(formId, formData, language = 'en') {
    return axios.put(baseUrl + `/api/v1/forms/${formId}?language=${language}`, formData, {
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

function deleteForm(formId) {
    return axios.delete(baseUrl + `/api/v1/forms/${formId}`, {
        headers: authHeader()
    })
    .then(function(response) {
        return {
            success: true,
            error: "",
            statusCode: response.status
        };
    })
    .catch(function(error) {
        return {
            success: false,
            error: extractErrorMessage(error),
            statusCode: error.response && error.response.status
        };
    });
}

function getFormStructure(formId, language = 'en', includeInactive = false) {
    const includeInactiveParam = includeInactive ? '&include_inactive=true' : '';
    
    return axios.get(baseUrl + `/api/v1/forms/${formId}/structure?language=${language}${includeInactiveParam}`, {
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

function updateFormStructure(formId, structureData, language = 'en') {
    return axios.put(baseUrl + `/api/v1/forms/${formId}/structure?language=${language}`, structureData, {
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
