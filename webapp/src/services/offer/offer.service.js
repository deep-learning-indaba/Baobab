import axios from "axios";
import {authHeader} from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const offerServices = {
    getOffer,
    addOffer,
    updateOffer
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

function addOffer(user_id, event_id, offer_date, expiry_date, payment_required, awards){
  let data = {
        user_id:user_id, 
        event_id:event_id,
        offer_date:offer_date,
        expiry_date:expiry_date,
        payment_required:payment_required,
        awards:awards
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

function updateOffer(offer_id, event_id, candidate_response, rejected_reason, awards){
    let data = {
        offer_id:offer_id, 
        event_id:event_id,
        candidate_response:candidate_response,
        rejected_reason:rejected_reason,
        awards:awards
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
