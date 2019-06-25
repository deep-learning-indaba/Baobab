import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const profileService = {
    getProfilesList,
    getUserProfile,
    getUserReview
}

function getProfilesList(event_id){
    return axios
        .get(baseUrl+"/api/v1/userprofilelist?event_id="+event_id, { headers: authHeader()})
        .then((response)=>{
            return { List: response.data, error: ""};
         })
        .catch((error)=>{
            //handling an error, then assign an empty / null array
            return {List:[],
                     error: error.response && error.response.data
                      ? error.response.data.message :
                         error.message }
        });
}

function getUserProfile(user_id){
    return axios
        .get(baseUrl+"/api/v1/userprofile?user_id="+user_id,{headers: authHeader()})
        .then((response)=>{
            return response.data;
        })
        .catch((error)=>{
            return { user:{},
                error: error.response && error.response.data ?
                error.response.data.message:
                error.message }
        });
}

function getUserReview(event_id,user_id) {
    return axios
      .get(baseUrl + "/api/v1/user-review?event_id="+event_id+"&user_id="+user_id,{ headers: authHeader() })
      .then(response => {
            return response.data;
        })
        .catch((error)=>{
            return { applicationReviewList:{},
                error: error.response && error.response.data ?
                error.response.data.message:
                error.message }
        });
}
