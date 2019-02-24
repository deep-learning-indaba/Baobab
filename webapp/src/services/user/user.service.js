import axios from "axios";
const baseUrl = process.env.REACT_APP_API_URL;
export const userService = {
  login,
  logout,
  create
};

export function authHeader() {
  // return authorization header with basic auth credentials
  let user = JSON.parse(localStorage.getItem("user"));

  if (user) {
    return { Authorization: user.token };
  } else {
    return {};
  }
}

function login(email, password) {
  return axios
    .post(baseUrl + `/api/v1/authenticate`, {
      email: email,
      password: password
    })
    .then(response => {
      let user = null;
      if (response) user = response.data;

      // login successful if there's a user in the response
      if (user) {
        // store user details in local storage
        localStorage.setItem("user", JSON.stringify(user));
      }

      return {
        user: user,
        status: response.status,
        message: response.statusText
      };
    })
    .catch(error => {
      if (error.response) {
        return {
          user: null,
          status: error.response.status,
          message: error.response.statusText
        };
      } else {
        // The request was made but no response was received
        return {
          user: null,
          status: null,
          message: error.message
        };
      }
    });
}

function create(user) {
  return axios
    .post(baseUrl + `/api/v1/user`, {
      email: user.email,
      firstname: user.firstName,
      lastname: user.lastName,
      user_title: user.title,
      nationality_country_id: user.nationality,
      residence_country_id: user.residence,
      user_ethnicity: user.ethnicity,
      user_gender: user.gender,
      affiliation: user.affiliation,
      department: user.department,
      user_disability: user.disability,
      user_category_id: user.category,
      password: user.password
    })
    .then(response => {
      let user = null;
      if (response) user = response.data;
      // login successful if there's a user in the response
      if (user) {
        // store user details in local storage
        localStorage.setItem("user", JSON.stringify(user));
      }

      return user;
    });
}

function logout() {
  // remove user from local storage to log user out
  localStorage.removeItem("user");
}
