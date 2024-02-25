import axios from 'axios';
import {authHeader} from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const applicationFormService = {
    getForEvent,
    submit,
    getResponse,
    updateResponse,
    withdraw,
    getQuestionList,
    getDetailsForEvent,
    updateApplicationForm
};


function getForEvent(eventId) {
    const headers = {
      ...authHeader(),
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache',
      'Expires': '0',
    };

    return axios
    .get(baseUrl + "/api/v1/application-form?event_id=" + eventId, { 'headers': headers })
    .then(response => {
        let formSpec = null;
        if (response) formSpec = response.data;
        return {
            formSpec: formSpec,
            status: response.status,
            message: response.statusText
        }
    })
    .catch(function(error){
      return{
        formSpec:null,
        error:
          error.response && error.response.data
          ? error.response.data.message
          : error.message,
        status: error.response && error.response.status
      };
  });
}

function getResponse(eventId) {
  return axios
    .get(baseUrl + "/api/v1/response?event_id=" + eventId, { 'headers': authHeader() })
    .then(resp => {
        let response = null;
        if (resp) response = resp.data;
        return {
            response: response,
            status: resp.status,
            message: resp.statusText
        }
    })
    .catch(error => {
      if (error.response) {
        return {
            response: null,
            status: error.response.status,
            message: error.response.statusText
        };
      } else {
        // The request was made but no response was received
        return {
          response: null,
          status: null,
          message: error.message
        };
      }
    });
}

function submit(applicationFormId, isSubmitted, answers) {
    let response = {
      "application_form_id": applicationFormId,
      "is_submitted": isSubmitted,
      "answers": answers
    }

    return axios.post(baseUrl + `/api/v1/response`, response, {headers: authHeader()})
      .then(resp=> {
        return {
          response_id: resp.data.id,
          is_submitted: resp.data.is_submitted,
          submitted_timestamp: resp.data.submitted_timestamp,
          status: response.status,
          message: response.statusText
        };
      })
      .catch(error => {
        if (error.response) {
          return {
            response_id: null,
            status: error.response.status,
            message: error.response.statusText,
            is_submitted: false,
            submitted_timestamp: null
          };
        } else {
          // The request was made but no response was received
          return {
            response_id: null,
            status: null,
            message: error.message,
            is_submitted: false,
            submitted_timestamp: null
          };
        }
      })
}



function updateResponse(response_id, applicationFormId, isSubmitted, answers) {
  let response = {
    "id": response_id,
    "application_form_id": applicationFormId,
    "is_submitted": isSubmitted,
    "answers": answers
  }

  return axios.put(baseUrl + `/api/v1/response`, response, {headers: authHeader()})
    .then(resp=> {
      return {
        response_id: resp.data.id,
        is_submitted: resp.data.is_submitted,
        submitted_timestamp: resp.data.submitted_timestamp,
        status: response.status,
        message: response.statusText,
      };
    })
    .catch(error => {
      if (error.response) {
        return {
          response_id: null,
          status: error.response.status,
          message: error.response.statusText,
          is_submitted: response.is_submitted,
          submitted_timestamp: null
        };
      } else {
        // The request was made but no response was received
        return {
          response_id: response.id,
          status: null,
          message: error.message,
          is_submitted: response.is_submitted,
          submitted_timestamp: null
        };
      }
    })
  }
  
function withdraw(id) {
  return axios.delete(baseUrl + `/api/v1/response`, {'headers': authHeader(), 'data': {'id': id} })
      .then(resp=> {
        return {
          isError: false,
          status: resp.status,
          message: resp.statusText
        };
      })
      .catch(error => {
        if (error.response) {
          return {
            isError: true,
            status: error.response.status,
            message: error.response.statusText,
          };
        } else {
          // The request was made but no response was received
          return {
            isError: true,
            status: null,
            message: error.message,
          };
        }
      });
}

function getQuestionList(eventId) {
  return axios
    .get(baseUrl + "/api/v1/questions", { 
        "headers": authHeader(),
        "params": {
            event_id: eventId
        }
    })
    .then(response => {
        let questions = null;
        if (response) questions = response.data;
        return {
            questions: questions,
            status: response.status,
            message: response.statusText
        }
    })
    .catch(function(error){
        return{
            questions: null,
            error:
                error.response && error.response.data
                ? error.response.data.message
                : error.message,
            status: error.response && error.response.status
        };
    });
}

function getDetailsForEvent(eventId) {
  return axios
  .get(baseUrl + "/api/v1/application-form-detail?event_id=" + eventId,
    { 'headers': authHeader() })
  .then(response => {
      let formSpec = null;
      if (response) formSpec = response.data;
      return {
          formSpec: formSpec,
          status: response.status,
          message: response.statusText
      }
  })
  .catch(function(error){
    return{
      formSpec:null,
      error:
        error.response && error.response.data
        ? error.response.data.message
        : error.message,
      status: error.response && error.response.status
    };
  });
}

export function updateApplicationForm(id, event_id, is_open, nominations, sections) {
  let form = {
    "id": id,
    'event_id': event_id,
    "is_open": is_open,
    "nominations": nominations,
    "sections": sections
  }

  return axios.put(baseUrl + `/api/v1/application-form-detail`, form, {headers: authHeader()})
    .then(resp=> {
      return resp;
    })
    .catch(error => {
      if (error.response) {
        return error.response;
      } else {
        // The request was made but no response was received
        return error;
      }
    })
  }

  export function createApplicationForm(event_id, is_open, nominations, sections) {
    let form = {
      'event_id': event_id,
      "is_open": is_open,
      "nominations": nominations,
      "sections": sections
    }
  
    return axios.post(baseUrl + `/api/v1/application-form-detail`, form, {headers: authHeader()})
      .then(resp=> {
        return resp;
      })
      .catch(error => {
        if (error.response) {
          return error.response;
        } else {
          // The request was made but no response was received
          return error;
        }
      })
    }