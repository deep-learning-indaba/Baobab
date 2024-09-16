import axios from "axios";
import {authHeader} from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const outcomeService = {
    getOutcome,
    assignOutcome,
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
  const data = { user_id, event_id, outcome };
  if (reason) {
      data.reason = reason;
  }

  return axios.post(`${baseUrl}/api/v1/outcome`, data, {  
      headers: authHeader(),
  })
  .then(response => ({
      status: response.status,
      outcome: response.data
  }))
  .catch(error => ({
      message: null,
      error: error.response && error.response.data
          ? error.response.data.message
          : error.message
  }));
}