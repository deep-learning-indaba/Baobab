import axios from "axios";
import { authHeader } from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const invitedGuestServices = {
    getInvitedGuestList,
    addInvitedGuest,
    createInvitedGuest
}

function getInvitedGuestList(eventId) {
    return axios
      .get(baseUrl + "/api/v1/invitedGuestList?event_id=" + eventId , {
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

  function addInvitedGuest(email_address, event_Id, role) {
    let data = {
      event_id: event_Id,
      email_address : email_address,
      role: role,
    };
    return axios
        .post(baseUrl + "/api/v1/invitedGuest", data, { headers: authHeader() })
        .then(function(response) {
            return {
              msg: "succeeded",
              response: response
            }
        })
        .catch(function(error) {
          if(error.response.status === 404){
            console.log(error.response.status)
            return {msg: "404"}
          }
          else{
            return {
                msg: "Failed",
                error: (error.response && error.response.data) ? error.response.data.message : error.message,
            }
          }
        })
}


function createInvitedGuest(email_address, event_Id, role) {
  let data = {
    event_id: event_Id,
    email_address : email_address,
    role: role,
  };
  return axios
      .post(baseUrl + "/api/v1/invitedGuest/create", data, { headers: authHeader() })
      .then(function(response) {
          return {
            msg: "succeeded",
            response: response
          }
      })
      .catch(function(error) {
        if(error.response.status === 404){
          console.log(error.response.status)
          return {msg: "404"}
        }
        else{
          return {
              msg: "Failed",
              error: (error.response && error.response.data) ? error.response.data.message : error.message,
          }
        }
      })
}