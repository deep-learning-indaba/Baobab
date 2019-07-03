import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const registrationService = {
  getRegistrationForm,
  getRegistrationResponse,
  submitResponse,
  requestInvitationLetter
};

function getRegistrationForm(eventId, offerId) {
  return axios
    .get(
      baseUrl +
        "/api/v1/registration-form?event_id=" +
        eventId +
        "&offer_id=" +
        offerId,
      {
        headers: authHeader()
      }
    )
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

function submitResponse(data, shouldUpdate) {
  const promise = shouldUpdate
    ? axios.put(baseUrl + "/api/v1/registration-response", data, {
        headers: authHeader()
      })
    : axios.post(baseUrl + "/api/v1/registration-response", data, {
        headers: authHeader()
      });
  return promise
    .then(function(response) {
      return {
        error: "",
        form: response
      };
    })
    .catch(function(error) {
      return {
        error:
          error.response && error.response.data && error.respose.data.message
            ? error.response.data.message
            : error.message
      };
    });
}

function requestInvitationLetter(user) {
  let invitationLetterReq = {
    work_address: user.fullWorkAddress,
    addressed_to: user.letterAddressedTo,
    residential_address: user.fullResidentialAddress,
    passport_name: user.fullNameOnPassport,
    passport_no: user.passportNumber,
    passport_issued_by: user.passportIssuedBy,
    passport_expiry_date: user.passportExpiryDate
  };
  return axios
    .post(baseUrl + `/api/v1/invitation-letter`, invitationLetterReq, {
      headers: authHeader()
    })
    .then(response => {
      return {
        invitationLetterId: response.invitation_letter_request_id,
        status: response.status,
        message: response.statusText
      };
    })
    .catch(error => {
      if (error.response) {
        return {
          invitationLetterId: null,
          status: error.response.status,
          message: error.response.statusText,
          is_submitted: false
        };
      } else {
        return {
          invitationLetterId: null,
          status: null,
          message: error.message
        };
      }
    });
}
