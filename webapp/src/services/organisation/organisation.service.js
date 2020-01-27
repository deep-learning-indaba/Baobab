import axios from "axios";

const baseUrl = process.env.REACT_APP_API_URL;

export const organisationService = {
    getOrganisation
}

function getOrganisation() {
    return axios.get(baseUrl + "/api/v1/organisation")
        .then(function(response){
            return{
                organisation: response.data,
                error:"",
                statusCode: response.status
            };
        })
        .catch(function(error){
            return{
                organisation:null,
                error:
                    error.response && error.response.data
                        ? error.response.data.message
                        : error.message,
                statusCode: error.response && error.response.status
            };
        });
}

