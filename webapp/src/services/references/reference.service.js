import axios from "axios";
import { authHeader, extractErrorMessage } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const referenceService = {
    getReferenceRequestDetails,
    submitReference
}

function getReferenceRequestDetails(token){
    return axios
        .get(baseUrl+`/api/v1/reference-request/detail?token=${token}`,{headers: authHeader()})
        .then((response)=>{
            return {
                details: response.data,
                error: null
            }
        })
        .catch((error)=>{
            return {
                details: null,
                error: error.response && error.response.data ?
                    error.response.data.message:
                    error.message 
            }
        });
}

function submitReference(token, uploadedDocument, shouldUpdate) {
    let reference = {
        token: token,
        uploaded_document: uploadedDocument
      };

    const promise = shouldUpdate 
        ? axios.put(baseUrl + "/api/v1/reference", reference, { headers: authHeader() })
        : axios.post(baseUrl + "/api/v1/reference", reference, { headers: authHeader() })
    
    return promise
        .then(function(response) {
          return {
            error: ""
          };
        })
        .catch(function(error) {
          return {
            error: extractErrorMessage(error)    
          };
        });
}