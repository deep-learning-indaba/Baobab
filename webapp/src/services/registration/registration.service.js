import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const registrationService = {
  getRegistrationForm,
  getRegistrationResponse,
  submitResponse,
  getOffer
};

function getOffer(eventId) {
  return axios
    .get(baseUrl + "/api/v1/offer?event_id=" + eventId, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        form: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        form: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}


function getRegistrationForm(eventId, offerId) {
  return axios
    .get(baseUrl + "/api/v1/registration-form?event_id=" + eventId , + "?offer_id=" + offerId, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        form: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        form: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function getRegistrationResponse(id) {
  return axios
    .get(baseUrl + "/api/v1/registration-response?id=" + id, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        form: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        form: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function submitResponse(responseId, reviewFormId, scores, shouldUpdate) {
  let review = {
    response_id: responseId,
    review_form_id: reviewFormId,
    scores: scores
  };

  const promise = shouldUpdate 
      ? axios.put(baseUrl + "/api/v1/registartion-response", review, { headers: authHeader() })
      : axios.post(baseUrl + "/api/v1/registration-response", review, { headers: authHeader() })
  
  return promise
    .then(function(response) {
      return {
        error: ""
      };
    })
    .catch(function(error) {
      return {
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

