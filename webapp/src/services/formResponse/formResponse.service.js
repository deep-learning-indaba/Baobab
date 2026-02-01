import axios from "axios";
import { authHeader, extractErrorMessage } from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const formResponseService = {
    createResponse,
    updateResponse,
    getResponse,
    getResponses,
    submitResponse,
    withdrawResponse,
    getResponseListAdmin,
    getResponseDetailAdmin
}

/**
 * Create a new form response
 * @param {number} formId - The form ID
 * @param {object} data - Response data { language, answers: [{question_id, value}] }
 * @returns {Promise} Response with response object or error
 */
function createResponse(formId, data) {
    return axios.post(baseUrl + `/api/v1/forms/${formId}/responses`, data, {
        headers: authHeader()
    })
    .then(function(response) {
        return {
            response: response.data,
            error: "",
            statusCode: response.status
        };
    })
    .catch(function(error) {
        return {
            response: null,
            error: extractErrorMessage(error),
            statusCode: error.response && error.response.status,
            responseId: error.response && error.response.data && error.response.data.response_id
        };
    });
}

/**
 * Update an existing form response
 * @param {number} formId - The form ID
 * @param {number} responseId - The response ID
 * @param {object} data - Response data { answers: [{question_id, value}] }
 * @returns {Promise} Response with updated response object or error
 */
function updateResponse(formId, responseId, data) {
    const payload = {
        ...data,
        response_id: responseId
    };
    
    return axios.put(baseUrl + `/api/v1/forms/${formId}/responses`, payload, {
        headers: authHeader()
    })
    .then(function(response) {
        return {
            response: response.data,
            error: "",
            statusCode: response.status
        };
    })
    .catch(function(error) {
        return {
            response: null,
            error: extractErrorMessage(error),
            statusCode: error.response && error.response.status
        };
    });
}

/**
 * Get user's response(s) for a form
 * @param {number} formId - The form ID
 * @returns {Promise} Response with response object(s) or error
 */
function getResponse(formId) {
    return axios.get(baseUrl + `/api/v1/forms/${formId}/responses`, {
        headers: authHeader()
    })
    .then(function(response) {
        // Backend returns either single response or {responses: [...]}
        if (response.data.responses) {
            // Multiple responses mode
            return {
                responses: response.data.responses,
                response: response.data.responses.length > 0 ? response.data.responses[0] : null,
                multiple: true,
                error: "",
                statusCode: response.status
            };
        } else {
            // Single response mode
            return {
                response: response.data,
                responses: [response.data],
                multiple: false,
                error: "",
                statusCode: response.status
            };
        }
    })
    .catch(function(error) {
        return {
            response: null,
            responses: [],
            multiple: false,
            error: extractErrorMessage(error),
            statusCode: error.response && error.response.status
        };
    });
}

/**
 * Get all responses for a form (when multiple_responses is true)
 * Same as getResponse but explicitly returns array
 * @param {number} formId - The form ID
 * @returns {Promise} Response with responses array or error
 */
function getResponses(formId) {
    return getResponse(formId).then(result => {
        return {
            responses: result.responses || [],
            error: result.error,
            statusCode: result.statusCode
        };
    });
}

/**
 * Submit a form response
 * @param {number} formId - The form ID
 * @param {number} responseId - The response ID
 * @returns {Promise} Response with submitted response object or error
 */
function submitResponse(formId, responseId) {
    return axios.post(baseUrl + `/api/v1/forms/${formId}/responses/${responseId}/submit`, {}, {
        headers: authHeader()
    })
    .then(function(response) {
        return {
            response: response.data,
            error: "",
            statusCode: response.status
        };
    })
    .catch(function(error) {
        // Extract validation errors if present
        let validationErrors = null;
        if (error.response && error.response.data && error.response.data.details) {
            validationErrors = error.response.data.details;
        }
        
        return {
            response: null,
            error: extractErrorMessage(error),
            statusCode: error.response && error.response.status,
            validationErrors: validationErrors
        };
    });
}

/**
 * Withdraw a submitted form response
 * @param {number} formId - The form ID
 * @param {number} responseId - The response ID
 * @returns {Promise} Response with withdrawn response object or error
 */
function withdrawResponse(formId, responseId) {
    return axios.post(baseUrl + `/api/v1/forms/${formId}/responses/${responseId}/withdraw`, {}, {
        headers: authHeader()
    })
    .then(function(response) {
        return {
            response: response.data,
            error: "",
            statusCode: response.status
        };
    })
    .catch(function(error) {
        return {
            response: null,
            error: extractErrorMessage(error),
            statusCode: error.response && error.response.status
        };
    });
}

/**
 * Get paginated list of all responses for a form (admin only)
 * @param {number} eventId - The event ID
 * @param {number} formId - The form ID
 * @param {object} filters - Filters { page, per_page, is_submitted, is_withdrawn, user_id, email, name }
 * @returns {Promise} Response with paginated responses or error
 */
function getResponseListAdmin(eventId, formId, filters = {}) {
    const params = new URLSearchParams();
    params.append('event_id', eventId);
    
    if (filters.page) params.append('page', filters.page);
    if (filters.per_page) params.append('per_page', filters.per_page);
    if (filters.is_submitted !== undefined) params.append('is_submitted', filters.is_submitted);
    if (filters.is_withdrawn !== undefined) params.append('is_withdrawn', filters.is_withdrawn);
    if (filters.user_id) params.append('user_id', filters.user_id);
    if (filters.email) params.append('email', filters.email);
    if (filters.name) params.append('name', filters.name);
    
    return axios.get(baseUrl + `/api/v1/forms/${formId}/responses/admin?${params.toString()}`, {
        headers: authHeader()
    })
    .then(function(response) {
        return {
            data: response.data,
            error: "",
            statusCode: response.status
        };
    })
    .catch(function(error) {
        return {
            data: null,
            error: extractErrorMessage(error),
            statusCode: error.response && error.response.status
        };
    });
}

/**
 * Get detailed response including answers and linked response (admin only)
 * @param {number} eventId - The event ID
 * @param {number} formId - The form ID
 * @param {number} responseId - The response ID
 * @returns {Promise} Response with detailed response object or error
 */
function getResponseDetailAdmin(eventId, formId, responseId) {
    const params = new URLSearchParams();
    params.append('event_id', eventId);
    
    return axios.get(baseUrl + `/api/v1/forms/${formId}/responses/${responseId}/admin?${params.toString()}`, {
        headers: authHeader()
    })
    .then(function(response) {
        return {
            response: response.data,
            error: "",
            statusCode: response.status
        };
    })
    .catch(function(error) {
        return {
            response: null,
            error: extractErrorMessage(error),
            statusCode: error.response && error.response.status
        };
    });
}
