import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const registrationAdminService = {
  getUnconfirmed,
  confirm
};

function getUnconfirmed(eventId) {
  return axios
    .get(baseUrl + "/api/v1/registration/unconfirmed?event_id=" + eventId, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        data: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        data: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
        statusCode: error.response && error.response.status
      };
    });
}

function confirm(registrationId) {
  const data = {
    registration_id: registrationId
  };

  return axios
    .post(baseUrl + "/api/v1/registration/confirm", data, {
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
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
        statusCode: error.response && error.response.status
      };
    });
}
