import axios from 'axios';
import {authHeader} from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const applicationFormService = {
    getForEvent,
    submit,
    getResponse,
    updateResponse
};


function getForEvent(eventId) {
    return axios
    .get(baseUrl + "/api/v1/application-form?event_id=" + eventId)
    .then(response => {
        let formSpec = null;
        if (response) formSpec = response.data;
        return {
            formSpec: formSpec,
            status: response.status,
            message: response.statusText
        }
    })
    .catch(error => {
      if (error.response) {
        return {
            formSpec: null,
            status: error.response.status,
            message: error.response.statusText
        };
      } else {
        // The request was made but no response was received
        return {
          formSpec: null,
          status: null,
          message: error.message
        };
      }
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
    // TODO: Handle put for updates
    let response = {
      "application_form_id": applicationFormId,
      "is_submitted": isSubmitted,
      "answers": answers
    }

    console.log("Submitting response: " + response);

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



function updateResponse(applicationFormId, isSubmitted, answers) {
  // TODO: Handle put for updates
  let response = {
    "application_form_id": applicationFormId,
    "is_submitted": isSubmitted,
    "answers": answers
  }

  console.log("Updating response: " + response);

  return axios.put(baseUrl + `/api/v1/response`, response, {headers: authHeader()})
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