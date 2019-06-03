import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const profileService = {
    getProfilesList
}

function getProfilesList(event_id){
    return axios
        .get(baseUrl+"/api/v1/userprofilelist?event_id="+event_id, { headers: authHeader()})
        .then((response)=>{
            return { List: response.data, error: ""};
         })
        .catch((error)=>{
            //handling an error, then assign an empty / null array
            return [], { error:error.message }
        });
}