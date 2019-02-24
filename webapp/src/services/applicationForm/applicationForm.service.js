import axios from 'axios';
const baseUrl = process.env.REACT_APP_API_URL;

export const applicationFormService = {
    getForEvent,
    submit
};


function getForEvent(eventId) {
    return axios
    .get(baseUrl + "/api/v1/application-form?event_id=" + eventId)
    .then(response => {
        let formSpec = null;
        if (response) formSpec = response.data;
        return {
            formSpec: formSpec,
            status: response.status,
            message: response.statusText
        }
    })
    .catch(error => {
      if (error.response) {
        return {
            formSpec: null,
            status: error.response.status,
            message: error.response.statusText
        };
      } else {
        // The request was made but no response was received
        return {
          formSpec: null,
          status: null,
          message: error.message
        };
      }
    });
}

function submit(response) {
    // TODO: Handle put for updates
    console.log("Submitting response: " + response);
    return axios.post(baseUrl + `/api/v1/response`, response)
      .then(resp=> {
        return {
          response_id: resp.data.id,
          status: response.status,
          message: response.statusText
        };
      })
      .catch(error => {
        if (error.response) {
          return {
            response_id: null,
            status: error.response.status,
            message: error.response.statusText
          };
        } else {
          // The request was made but no response was received
          return {
            response_id: null,
            status: null,
            message: error.message
          };
        }
      })
}