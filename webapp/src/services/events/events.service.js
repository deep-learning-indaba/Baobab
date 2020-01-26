import axios from "axios";
import { authHeader } from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const eventService = {
    getEvents,
    getByKey
}

function getEvents() {
    return axios
        .get(baseUrl + `/api/v1/events`, { 'headers': authHeader() })
        .then(function(response){
            return{
                events: response.data,
                error:"",
                statusCode: response.status
            };
          })
          .catch(function(error){
              return{
                events:null,
                error:
                  error.response && error.response.data
                  ? error.response.data.message
                  : error.message,
                statusCode: error.response && error.response.status
              };
          });
}

function getByKey(event_key) {
    return axios
        .get(baseUrl + `/api/v1/events`, { 'headers': authHeader() })  // TODO: Update to event key API
        .then(function(response){
            return{
                event: response.data.find(d=>d.description.toLowerCase().includes(event_key)),
                error:"",
                statusCode: response.status
            };
          })
          .catch(function(error){
              return{
                event:null,
                error:
                  error.response && error.response.data
                  ? error.response.data.message
                  : error.message,
                statusCode: error.response && error.response.status
              };
          });
}