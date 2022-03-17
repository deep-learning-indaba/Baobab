import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const attendanceService = {
  getAttendanceList,
  confirm,
  undoConfirmation,
};

function getAttendanceList(eventId, exclude_already_signed_in) {
  return axios
    .get(
      baseUrl +
        "/api/v1/registration/confirmed?event_id=" +
        eventId +
        "&exclude_already_signed_in=" +
        exclude_already_signed_in,
      {
        headers: authHeader(),
      }
    )
    .then(function (response) {
      return {
        data: response.data,
        error: "",
      };
    })
    .catch(function (error) {
      return {
        data: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
        statusCode: error.response && error.response.status,
      };
    });
}

function confirm(eventId, userId) {
  const data = {
    user_id: userId,
    event_id: eventId,
  };

  return axios
    .post(baseUrl + "/api/v1/attendance", data, {
      headers: authHeader(),
    })
    .then(function (response) {
      return {
        data: response.data,
        error: "",
        statusCode: response.status,
      };
    })
    .catch(function (error) {
      return {
        data: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
        statusCode: error.response && error.response.status,
      };
    });
}

function undoConfirmation(eventId, userId) {
  const data = {
    user_id: userId,
    event_id: eventId,
  };
  return axios
    .delete(baseUrl + `/api/v1/attendance`, { headers: authHeader(), data })
    .then(function (response) {
      return {
        data: response.data,
        error: "",
        statusCode: response.status,
      };
    })
    .catch(function (error) {
      return {
        data: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
        statusCode: error.response && error.response.status,
      };
    });
}
