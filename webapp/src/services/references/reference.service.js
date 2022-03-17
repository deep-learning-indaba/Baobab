import axios from "axios";
import { authHeader, extractErrorMessage } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const referenceService = {
  getReferenceRequestDetails,
  submitReference,
  getReferenceRequests,
  requestReference,
};

function getReferenceRequestDetails(token) {
  return axios
    .get(baseUrl + `/api/v1/reference-request/detail?token=${token}`, {
      headers: authHeader(),
    })
    .then((response) => {
      return {
        details: response.data,
        error: "",
      };
    })
    .catch((error) => {
      return {
        details: null,
        error: extractErrorMessage(error),
      };
    });
}

function submitReference(token, uploadedDocument, shouldUpdate) {
  let reference = {
    token: token,
    uploaded_document: uploadedDocument,
  };

  const promise = shouldUpdate
    ? axios.put(baseUrl + "/api/v1/reference", reference, {
        headers: authHeader(),
      })
    : axios.post(baseUrl + "/api/v1/reference", reference, {
        headers: authHeader(),
      });

  return promise
    .then(function (response) {
      return {
        error: "",
      };
    })
    .catch((error) => {
      return {
        error: extractErrorMessage(error),
      };
    });
}

function getReferenceRequests(responseId) {
  return axios
    .get(baseUrl + `/api/v1/reference-request/list?response_id=${responseId}`, {
      headers: authHeader(),
    })
    .then(function (response) {
      return {
        requests: response.data,
        error: "",
      };
    })
    .catch(function (error) {
      return {
        requests: null,
        error: extractErrorMessage(error),
        statusCode: error.response && error.response.status,
      };
    });
}

function requestReference(
  responseId,
  title,
  firstname,
  lastname,
  email,
  relation
) {
  let data = {
    response_id: responseId,
    title: title,
    firstname: firstname,
    lastname: lastname,
    email: email,
    relation: relation,
  };

  return axios
    .post(baseUrl + "/api/v1/reference-request", data, {
      headers: authHeader(),
    })
    .then(function (response) {
      return {
        error: "",
        referenceRequest: response.data,
      };
    })
    .catch(function (error) {
      return {
        error: extractErrorMessage(error),
      };
    });
}
