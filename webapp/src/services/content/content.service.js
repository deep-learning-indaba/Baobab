import axios from "axios";
const baseUrl = process.env.REACT_APP_API_URL;

export function getContent(type) {
  return axios
    .get(baseUrl + `/api/v1/content/` + type)
    .then(function(response) {
      // handle success
      // conso0le.log(JSON.stringify(response));
      return response.data;
    })
    .catch(function(error) {
      // handle error
      return { error: error };
      console.log(error);
    });
}
