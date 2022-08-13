import axios from "axios";
import { authHeader, extractErrorMessage } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const attendanceService = {
  getAttendanceList,
  confirm,
  undoConfirmation,
  getIndemnityForm,
  postIndemnity
};

function getAttendanceList(eventId, excludeCheckedIn) {
  return axios
    .get(
      baseUrl +
        "/api/v1/guestlist?event_id=" +
        eventId +
        "&exclude_already_checked_in=" +
        excludeCheckedIn,
      {
        headers: authHeader()
      }
    )
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

function confirm(eventId, userId) {
  const data = {
    user_id: userId,
    event_id: eventId
  };

  return axios
    .post(baseUrl + "/api/v1/attendance", data, {
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

function undoConfirmation(eventId, userId) {
  const data = {
    user_id: userId,
    event_id: eventId
  };
  return axios
    .delete(baseUrl + `/api/v1/attendance`, { headers: authHeader(), data })
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


function getIndemnityForm(eventId) {
  return axios
    .get(baseUrl + `/api/v1/indemnity?event_id=${eventId}`, { headers: authHeader() })
    .then((response) => {
        return {
            data: response.data,
            error: ""
        }
    })
    .catch((error) => {
        return {
            data: null,
            error: extractErrorMessage(error)
        }
    });
}

function postIndemnity(eventId) {
  return axios
    .post(baseUrl + "/api/v1/indemnity", {event_id: eventId}, { headers: authHeader() })
    .then((response) => {
      return {
          data: response.data,
          error: ""
      }
    })
    .catch((error) => {
        return {
            data: null,
            error: extractErrorMessage(error)
        }
    });
}