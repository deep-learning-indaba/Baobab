import axios from "axios";
import {authHeader} from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const outcomeService = {
    getOutcome,
    assignOutcome,
    resubmit
}

function getOutcome(event_id, user_id){
    return axios.get(baseUrl + "/api/v1/outcome?event_id=" +event_id +
    "&user_id=" +user_id ,{
        headers: authHeader()
      })
      .then(function(response){
        return{
            outcome: response.data,
            status: response.status
        };
      })
      .catch(function(error){
          return{
            outcome:null,
            error:
              error.response && error.response.data
              ? error.response.data.message
              : error.message,
            status: error.response && error.response.status
          };
      });
}

function assignOutcome(user_id, event_id, outcome, reason = null) {
  const params = {
      outcome: outcome,
      event_id: event_id,
      user_id: user_id
  };
  
  if (reason) {
      params.reason = reason;
  }

  return axios
      .post(`${baseUrl}/api/v1/outcome`, null, { 
          headers: authHeader(),
          params: params
      })
      .then(function (response) {
          return {
              status: response.status,
              outcome: response.data
          }
      })
      .catch(function(error) {
          return {
              message: null,
              error:
                  error.response && error.response.data
                  ? error.response.data.message
                  : error.message
          };
      });
}

function resubmit(user_id, event_id, response_id) {
    return axios
        .post(`${baseUrl}/api/v1/outcome/resubmit`, null, { 
            headers: authHeader(),
            params: {
                user_id: user_id,
                event_id: event_id,
                response_id: response_id
            }
        })
        .then(function (response) {
            return {
                newResponseId: response.data.new_response_id
            }
        })
        .catch(function(error) {
            return {
                error:
                    error.response && error.response.data
                    ? error.response.data.message
                    : error.message
            };
        });
}