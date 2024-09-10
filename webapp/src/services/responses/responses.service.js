import axios from 'axios';
import {authHeader} from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const responsesService = {
    getResponseList,
    getResponseDetail,
    tagResponse,
    removeTag,
    getComments,
    postComment,
    deleteComment
}

function getResponseList(eventId, includeUnsubmitted, questionIds) {
    return axios
        .get(baseUrl + "/api/v1/responses", { 
            "headers": authHeader(),
            "params": {
                event_id: eventId,
                include_unsubmitted: includeUnsubmitted,
                question_ids: questionIds
            }
        })
        .then(response => {
            let responses = null;
            if (response) responses = response.data;
            return {
                responses: responses,
                status: response.status,
                message: response.statusText
            }
        })
        .catch(function(error){
            return{
                responses: null,
                error:
                    error.response && error.response.data
                    ? error.response.data.message
                    : error.message,
                status: error.response && error.response.status
            };
        });
}

function getResponseDetail(responseId, eventId) {
    return axios
        .get(baseUrl + "/api/v1/responsedetail", { 
            "headers": authHeader(),
            "params": {
                response_id: responseId,
                event_id: eventId
            }
        })
        .then(response => {
            let detail = null;
            if (response) detail = response.data;
            return {
                detail: detail,
                status: response.status,
                message: response.statusText
            }
        })
        .catch(function(error){
            return{
                detail: null,
                error:
                    error.response && error.response.data
                    ? error.response.data.message
                    : error.message,
                status: error.response && error.response.status
            };
        });
}

function tagResponse(responseId, tagId, eventId) {
    return axios
        .post(baseUrl + "/api/v1/responsetag", {
            response_id: responseId,
            tag_id: tagId,
            event_id: eventId
        }, { 
            "headers": authHeader()
        })
        .then(response => {
            let responseTag = null;
            if (response) responseTag = response.data;
            return {
                responseTag: responseTag,
                status: response.status,
                message: response.statusText
            }
        })
        .catch(function(error){
            return{
                responseTag: null,
                error:
                    error.response && error.response.data
                    ? error.response.data.message
                    : error.message,
                status: error.response && error.response.status
            };
        });
}

function removeTag(responseId, tagId, eventId) {
    return axios
        .delete(baseUrl + "/api/v1/responsetag", { 
            "headers": authHeader(),
            "params": {
                response_id: responseId,
                tag_id: tagId,
                event_id: eventId
            }
        })
        .then(response => {
            return {
                status: response.status,
                message: response.statusText
            }
        })
        .catch(function(error){
            return{
                error:
                    error.response && error.response.data
                    ? error.response.data.message
                    : error.message,
                status: error.response && error.response.status
            };
        });
}

function getComments(eventId, responseId) {
    return axios
        .get(`${baseUrl}/api/v1/comments`, {
            headers: authHeader(),
            params: {
                event_id: eventId,
                response_id: responseId
            }
        })
        .then(response => {
            return {
                comments: response.data,
                status: response.status,
                message: response.statusText
            };
        })
        .catch(error => {
            return {
                comments: null,
                error: error.response && error.response.data
                    ? error.response.data.message
                    : error.message,
                status: error.response && error.response.status
            };
        });
}

function postComment(eventId, responseId, content) {
    return axios
        .post(`${baseUrl}/api/v1/comments`, {
            event_id: eventId,
            response_id: responseId,
            content: content
        }, {
            headers: authHeader()
        })
        .then(response => {
            return {
                comment: response.data,
                status: response.status,
                message: response.statusText
            };
        })
        .catch(error => {
            return {
                comment: null,
                error: error.response && error.response.data
                    ? error.response.data.message
                    : error.message,
                status: error.response && error.response.status
            };
        });
}

function deleteComment(commentId) {
    return axios
        .delete(`${baseUrl}/api/v1/comments/${commentId}`, {
            headers: authHeader()
        })
        .then(response => {
            return {
                status: response.status,
                message: response.statusText
            };
        })
        .catch(error => {
            return {
                error: error.response && error.response.data
                    ? error.response.data.message
                    : error.message,
                status: error.response && error.response.status
            };
        });
}