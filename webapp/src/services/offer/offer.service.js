import axios from "axios";
import {authHeader, extractErrorMessage} from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const offerServices = {
    getOffer,
    addOffer,
    updateOffer,
    getOfferList
}

function getOffer(event_id){
    return axios.get(baseUrl + "/api/v1/offer?event_id=" +event_id,{
        headers: authHeader()
      })
      .then(function(response){
        return{
            offer: response.data,
            error:"",
            statusCode: response.status
        };
      })
      .catch(function(error){
          return{
            offer:null,
            error:
              error.response && error.response.data
              ? error.response.data.message
              : error.message,
            statusCode: error.response && error.response.status
          };
      });

}

function addOffer(user_id, event_id, offer_date, expiry_date, payment_required, grant_tags){
  const data = {
        user_id: user_id, 
        event_id: event_id,
        offer_date: offer_date,
        expiry_date: expiry_date,
        payment_required: payment_required,
        grant_tags: grant_tags
    }

    return axios
        .post(baseUrl + 'api/v1/offer',data,{headers:authHeader()})
        .then(function (response){
            return{
                message:"succeeded",
                response: response
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

function updateOffer(offer_id, event_id, candidate_response, rejected_reason, grant_tags){
    let data = {
        offer_id:offer_id, 
        event_id:event_id,
        candidate_response:candidate_response,
        rejected_reason:rejected_reason,
        grant_tags:grant_tags
    };

    return axios
        .put(baseUrl + "/api/v1/offer", data,{ headers: authHeader() })
        .then(function(response){
            return{
                message:"succeeded",
                response:response
            }
        }).catch(function(error) {
            return {
              message: null,
              error:
                error.response && error.response.data
                  ? error.response.data.message
                  : error.message
            };
          });     
}

function getOfferList(eventId) {
  return axios
    .get(baseUrl + `/api/v1/offerlist?event_id=${eventId}`, { headers: authHeader() })
    .then((response) => {
        return {
          offers: response.data,
          error: ""
        }
    })
    .catch((error) => {
        return {
          offers: null,
          error: extractErrorMessage(error)
        }
    });
}
