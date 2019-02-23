import axios from "axios";
const baseUrl = process.env.REACT_APP_API_URL;

export function getContent(type) {
  return axios
    .get(baseUrl + `/api/v1/content/` + type)
    .then(response => {
      return response;
    })
    .catch(error => {
      return { error: error };
    });
}
