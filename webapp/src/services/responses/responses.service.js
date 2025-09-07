import axios from 'axios';
import {authHeader} from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const responsesService = {
    getResponseList,
    getResponseDetail,
    tagResponse,
    removeTag,
    updateResponse
}

function getResponseList(eventId, includeUnsubmitted, questionIds, page, perPage, nameSearch, emailSearch, tagId) {
    return axios
        .get(baseUrl + "/api/v1/responses", {
            "headers": authHeader(),
            "params": {
                event_id: eventId,
                include_unsubmitted: includeUnsubmitted,
                question_ids: questionIds,
                page: page,
                per_page: perPage,
                name_search: nameSearch,
                email_search: emailSearch,
                tag_id: tagId
            }
        })
        .then(response => {
            let data = null;
            if (response) data = response.data;
            return {
                responses: data.responses,
                pagination: data.pagination,
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

function updateResponse(responseId, eventId, language, is_submitted, is_withdrawn) {
    return axios
        .put(baseUrl + `/api/v1/responsedetail?event_id=${eventId}`, {
            response_id: responseId,
            language: language,
            is_submitted: is_submitted,
            is_withdrawn: is_withdrawn
        }, { 
            "headers": authHeader()
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