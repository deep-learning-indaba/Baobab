import axios from "axios";
import history from "../History";

export function authHeader() {
  // return authorization header with basic auth credentials
  let user = JSON.parse(localStorage.getItem("user"));

  if (user) {
    return { Authorization: user.token };
  } else {
    return {};
  }
}

axios.interceptors.response.use(
  response => {
    return response;
  },
  function(error) {
    if (
      error.response &&
      error.response.status === 401 &&
      error.response.type === "UNAUTHORIZED"
    ) {
      console.log("unauthorized, logging out ...");
      history.push("/login");
      localStorage.removeItem("user");
    }
    return error;
  }
);
