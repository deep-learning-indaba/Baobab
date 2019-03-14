import axios from "axios";
import { authHeader } from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;
export const userService = {
  login,
  logout,
  create,
  update,
  get,
  deleteAccount,
  requestPasswordReset,
  confirmPasswordReset,
  verifyEmail,
  resendVerification
};

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

      return user;
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
      user_dateOfBirth: user.dateOfBirth,
      user_primaryLanguage: user.primaryLanguage,
      password: user.password
    })
    .then(response => {
      let user = null;
      if (response) user = response.data;
      return user;
    });
}

function update(user) {
  return axios
    .put(baseUrl + `/api/v1/user`, {
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
      password: "",
    }, { headers: authHeader() })
    .then(response => {
      let user = null;
      if (response) user = response.data;
      return user;
    });
}

function deleteAccount() {
  return axios
    .delete(baseUrl + `/api/v1/user`, { 'headers': authHeader() })
    .then(response => {
      localStorage.removeItem("user");

      return {
        status: response.status,
        message: response.statusText
      };
    })
    .catch(error => {
      if (error.response) {
        return {
          status: error.response.status,
          message: error.response.data ? error.response.data.message : error.response.statusText
        };
      } else {
        // The request was made but no response was received
        return {
          status: null,
          message: error.message
        };
      }
    });
}

function logout() {
  // remove user from local storage to log user out
  localStorage.removeItem("user");
}

function get() {
  return axios
    .get(baseUrl + `/api/v1/user`, { 'headers': authHeader() })
    .then(function (response) {
      // handle success
      return response.data;
    })
    .catch(function (error) {
      // handle error
      return [], { error: error };
    });
}

function requestPasswordReset(email) {
  return axios
    .post(baseUrl + `/api/v1/password-reset/request`, {
      email: email,
    })
    .then(response => {
      return {
        status: response.status,
        message: response.statusText
      };
    })
    .catch(error => {
      if (error.response) {
        return {
          status: error.response.status,
          message: error.response.data ? error.response.data.message : error.response.statusText
        };
      } else {
        // The request was made but no response was received
        return {
          status: null,
          message: error.message
        };
      }
    });
}

function confirmPasswordReset(password, code) {
  return axios
    .post(baseUrl + `/api/v1/password-reset/confirm`, {
      password: password,
      code: code,
    })
    .then(response => {
      return {
        status: response.status,
        message: response.statusText
      };
    })
    .catch(error => {
      if (error.response) {
        return {
          status: error.response.status,
          message: error.response.data ? error.response.data.message : error.response.statusText
        };
      } else {
        // The request was made but no response was received
        return {
          status: null,
          message: error.message
        };
      }
    });
}

function verifyEmail(token) {
  console.log("Verifying email with token: " + token);
  return axios
    .get(baseUrl + "/api/v1/verify-email?token=" + token)
    .then(response => {
      return {
        error: ""
      };
    })
    .catch(error => {
      return {
        error: (error.response && error.response.data) ? error.response.data.message : error.message
      };
    });
}

function resendVerification(email) {
  return axios
    .get(baseUrl + "/api/v1/resend-verification-email?email=" + email)
    .then(response => {
      return {
        error: "",
      };
    })
    .catch(error => {
      return {
        error: (error.response && error.response.data) ? error.response.data.message : error.message
      };
    });
}