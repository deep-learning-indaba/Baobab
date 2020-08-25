import axios from "axios";
import history from "../History";
import i18n from 'i18next';

export function authHeader() {
  // return authorization header with basic auth credentials
  let user = JSON.parse(localStorage.getItem("user"));

  if (user) {
    return { Authorization: user.token };
  } else {
    return {};
  }
}

export function extractErrorMessage(error) {
  // Extract error message from error objects sent by the back-end
  return error.response && error.response.data
    ? error.response.data.message
    : error.message;
}

axios.interceptors.response.use(
  (response) => {
    return response;
  },
  function (error) {
    if (
      error &&
      error.response &&
      error.response.status === 401 &&
      error.response.data &&
      error.response.data.type === "UNAUTHORIZED"
    ) {
      // Redirect if you receive unauth, but only if you aren't on the home page
      if (history && history.location && history.location.pathname !== "/") {
        localStorage.removeItem("user");
        history.push("/login");
      }
    } else throw error;
  }
);

axios.interceptors.request.use(
  request => {
    request.params = request.params || {};
    request.params['language'] = i18n.language;
    return request;
  }
)
