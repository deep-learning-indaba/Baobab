import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const registrationService = {
  getRegistrationForm,
  getRegistrationResponse,
  submitResponse,
  determineIfGuest,
  getGuestRegistration,
  submitGuestResponse,
  getGuestRegistrationResponse
};

function getRegistrationForm(eventId, offerId) {
  return axios
    .get(baseUrl + "/api/v1/registration-form?event_id=" + eventId + "&offer_id=" + offerId, {
      headers: authHeader()
    })
    .then(function (response) {
      return {
        form: response.data,
        error: ""
      };
    })
    .catch(function (error) {
      return {
        form: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
        statusCode: error.response && error.response.status
      };
    });
}

function getRegistrationResponse(id) {
  return axios 
    .get(baseUrl + "/api/v1/registration-response", {
      headers: authHeader()
    })
    .then(function (response) {
      return {
        form: response.data,
        error: ""
      };

    },

    )
    .catch(function (error) {
      return {
        form: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function submitResponse(data, shouldUpdate) {

  const promise = shouldUpdate
    ? axios.put(baseUrl + "/api/v1/registration-response", data, { headers: authHeader() })
    : axios.post(baseUrl + "/api/v1/registration-response", data, { headers: authHeader() })
  return promise
    .then(function (response) {
      return {
        error: "",
        form: response
      };
    },
    )
    .catch(function (error) {
      return {
        error:
          error.response && error.response.data && error.respose.data.message
            ? error.response.data.message
            : error.message
      };
    });
}

function determineIfGuest(event_id) {
  return axios
    .get(baseUrl + "/api/v1/checkIfInvitedGuest?event_id="+event_id, { headers: authHeader() })
    .then(function (response) {
      return {
        msg: "Guest Found",
        statusCode: "200"
      }
    })
    .catch(function (error) {
      if (error.response && error.response.status === 404) {
        return {
          msg: "Guest Not Found",
          statusCode: "404"
        }
      } else {
        return {
          msg: "Failed",
          error: (error.response && error.response.data) ? error.response.data.message : error.message,
        }
      }
    })

}
function getGuestRegistration(event_id) {
  return axios
    .get(baseUrl + "/api/v1/guest-registration-form?event_id="+event_id, { headers: authHeader() })
    .then(function (response) {
      return {
        msg: "succeeded",
        form: response.data,
        
        error: ""
      }
    })
    .catch(function (error) {
      if (error.response && error.response.status === 404) {
        return { msg: "404" }
      } else {
        return {
          msg: "Failed",
          error: (error.response && error.response.data) ? error.response.data.message : error.message,
        }
      }
    })

}

function getGuestRegistrationResponse() {
  return axios
    .get(baseUrl + "/api/v1/guest-registration", {
      headers: authHeader()
    })
    .then(function (response) {
      return {
        form: response.data,
        error: ""
      };

    },

    )
    .catch(function (error) {
      return {
        form: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function submitGuestResponse(data, shouldUpdate) {

  const promise = shouldUpdate
    ? axios.put(baseUrl + "/api/v1/guest-registration", data, { headers: authHeader() })
    : axios.post(baseUrl + "/api/v1/guest-registration", data, { headers: authHeader() })
  return promise
    .then(function (response) {
      return {
        error: "",
        form: response
      };
    },
    )
    .catch(function (error) {
      return {
        error:
          error.response && error.response.data && error.respose.data.message
            ? error.response.data.message
            : error.message
      };
    });
}