import axios from "axios";

export function authHeader() {
  // return authorization header with basic auth credentials
  let user = JSON.parse(localStorage.getItem("user"));

  if (user) {
    return { Authorization: user.token };
  } else {
    return {};
  }
}

function errorResponseHandler(error) {
  if (error.response) {
    console.log(error.response.status);
    if (error.response.status === 401) {
      window.location = "/login";
    }
  }
}

// apply interceptor on response
axios.interceptors.response.use(response => response, errorResponseHandler);

export default errorResponseHandler;
