import axios from "axios";
import { authHeader } from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;
// const UNKNOWN_COUNTRY = 260;

export const invitedGuestServices = {
  getInvitedGuestList,
  addInvitedGuest,
  createInvitedGuest,
  getRoles,
  determineIfInvitedGuest,
  addTag
}

const roleOptions = [
  { value: "Speaker", label: "Speaker" },
  { value: "Guest", label: "Guest" },
  { value: "Mentor", label: "Mentor" },
  { value: "Friend of the Indaba", label: "Friend of the Indaba" },
  { value: "Organiser", label: "Organiser" },
  { value: "Dignitary", label: "Dignitary" },
  { value: "Indaba X", label: "Indaba X" },
  { value: "Sponsor", label: "Sponsor" },
  { value: "Press", label: "Press" }
];

function getRoles() {
  return roleOptions;
}

function getInvitedGuestList(eventId) {
  return axios
    .get(baseUrl + "/api/v1/invitedGuestList?event_id=" + eventId, {
      headers: authHeader()
    })  
    .then(function (response) {
      return {
        guests: response.data,
        error: ""
      };
    })
    .catch(function (error) {
      return {
        guests: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function addInvitedGuest(email_address, event_Id, role) {
  let data = {
    event_id: event_Id,
    email: email_address,
    role: role,
  };

  return axios
    .post(baseUrl + "/api/v1/invitedGuest", data, { headers: authHeader() })
    .then(function (response) {
      return {
        msg: "succeeded",
        response: response
      }
    })
    .catch(function (error) {
      if (error.response && error.response.status === 404) {
        return { msg: "404" }
      }
      else if (error.response && error.response.status === 409) {
        return { msg: "409" }
      }
      else {
        return {
          msg: "Failed",
          error: (error.response && error.response.data) ? error.response.data.message : error.message,
        }
      }
    })
}

function determineIfInvitedGuest(event_id) {
  return axios
    .get(baseUrl + "/api/v1/checkIfInvitedGuest?event_id=" + event_id, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        msg: "Guest Found",
        statusCode: "200"
      };
    })
    .catch(function(error) {
      if (error.response && error.response.status === 404) {
        return {
          msg: "Guest Not Found",
          statusCode: "404"
        };
      } else {
        return {
          msg: "Failed",
          error:
            error.response && error.response.data
              ? error.response.data.message
              : error.message
        };
      }
    });
}


function createInvitedGuest(user, event_Id, role) {
  let data = {
    event_id: event_Id,
    email: user.email,
    firstname: user.firstName,
    lastname: user.lastName,
    user_title: user.title,
    role: role,
    policy_agreed: true
  };
  
  return axios
    .post(baseUrl + "/api/v1/invitedGuest/create", data, { headers: authHeader() })
    .then(function (response) {

      return {
        msg: "succeeded",
        response: response
      }
    })
    .catch(function (error) {
      if (error.response && error.response.status === 409) {
        return { msg: "409" }
      } else {
        return {
          msg: "Failed",
          error: (error.response && error.response.data) ? error.response.data.message : error.message,
        }
      }
    })
}

function addTag(invitedGuestId, eventId, tagId) {
  console.log("addTag", invitedGuestId, eventId, tagId);
  let data = {
    tag_id: tagId,
    event_id: eventId,
    invited_guest_id: invitedGuestId
  };

  return axios
    .post(baseUrl + "/api/v1/invitedguesttag", data, { headers: authHeader() })
    .then(function (response) {
      return {
        msg: "succeeded",
        statusCode: response.status,
        response: response
      }
    })
    .catch(function (error) {
      return {
        msg: "Failed",
        statusCode: error.response && error.response.status,
        error: (error.response && error.response.data) ? error.response.data.message : error.message,
      }
    })
}