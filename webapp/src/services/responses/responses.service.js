import axios from 'axios';
import {authHeader} from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const responsesService = {
    getResponseList,
    getResponseDetail,
    tagResponse
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
        .get(baseUrl + "/api/v1/responsetag", { 
            "headers": authHeader(),
            "params": {
                response_id: responseId,
                tag_id: tagId,
                event_id: eventId
            }
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