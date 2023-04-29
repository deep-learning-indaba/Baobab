import axios from 'axios';
import {authHeader} from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const tagsService = {
    getTag,
    addTag,
    updateTag,
    getTagList,
    getTagListConfig,
    getTagTypeList
}

function getTag(tagId, eventId) {
    return axios
        .get(baseUrl + "/api/v1/tag", { 
            "headers": authHeader(),
            "params": {
                id: tagId,
                event_id: eventId
            }
        })
        .then(response => {
            let tag = null;
            if (response) tag = response.data;
            return {
                tag: tag,
                status: response.status,
                message: response.statusText
            }
        })
        .catch(function(error){
            return{
                tag: null,
                error:
                    error.response && error.response.data
                    ? error.response.data.message
                    : error.message,
                status: error.response && error.response.status
            };
        });
}

function addTag(tag, eventId) {
    return axios
        .post(baseUrl + "/api/v1/tag", tag, { 
            "headers": authHeader(),
            "params": {
                event_id: eventId
            }
        })
        .then(response => {
            let tag = null;
            if (response) tag = response.data;
            return {
                tag: tag,
                status: response.status,
                message: response.statusText
            }
        })
        .catch(function(error){
            return{
                tag: null,
                error:
                    error.response && error.response.data
                    ? error.response.data.message
                    : error.message,
                status: error.response && error.response.status
            };
        });
}

function updateTag(tag, eventId) {
    return axios
        .put(baseUrl + "/api/v1/tag", tag, { 
            "headers": authHeader(),
            "params": {
                event_id: eventId
            }
        })
        .then(response => {
            let tag = null;
            if (response) tag = response.data;
            return {
                tag: tag,
                status: response.status,
                message: response.statusText
            }
        })
        .catch(function(error){
            return{
                tag: null,
                error:
                    error.response && error.response.data
                    ? error.response.data.message
                    : error.message,
                status: error.response && error.response.status
            };
        });
}

function getTagList(eventId) {
    return axios
        .get(baseUrl + "/api/v1/tags", { 
            "headers": authHeader(),
            "params": {
                event_id: eventId            }
        })
        .then(response => {
            let tags = null;
            if (response) tags = response.data;
            return {
                tags: tags,
                status: response.status,
                message: response.statusText
            }
        })
        .catch(function(error){
            return{
                tags: null,
                error:
                    error.response && error.response.data
                    ? error.response.data.message
                    : error.message,
                status: error.response && error.response.status
            };
        });
}

function getTagTypeList(eventId) {
    return axios
    .get(baseUrl + "/api/v1/tagtypes", { 
        "headers": authHeader(),
        "params": {
            event_id: eventId
        }
    })
    .then(response => {
        let tag_types = null;
        if (response) tag_types = response.data;
        return {
            tag_types: tag_types,
            status: response.status,
            message: response.statusText
        }
    })
    .catch(function(error){
        return{
            tag_types: null,
            error:
                error.response && error.response.data
                ? error.response.data.message
                : error.message,
            status: error.response && error.response.status
        };
    });
}


function getTagListConfig(eventId) {
    return axios
        .get(baseUrl + "/api/v1/tagsconfig", { 
            "headers": authHeader(),
            "params": {
                event_id: eventId
            }
        })
        .then(response => {
            let tags = null;
            if (response) tags = response.data;
            return {
                tags: tags,
                status: response.status,
                message: response.statusText
            }
        })
        .catch(function(error){
            return{
                tags: null,
                error:
                    error.response && error.response.data
                    ? error.response.data.message
                    : error.message,
                status: error.response && error.response.status
            };
        });
}