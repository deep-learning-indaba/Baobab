import axios from "axios";
import { authHeader } from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const invitedGuestServices = {
    getInvitedGuestList
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