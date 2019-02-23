import axios from 'axios';
const baseUrl = process.env.REACT_APP_API_URL;

export const applicationFormService = {
    getForEvent,
    submit
};

// let dummyFormSpec = {
//     "eventId": 1,
//     "is_open": true,
//     "deadline": "2019-04-30",
//     sections: [
//         {
//             "sectionId": 1,
//             "name": "Section 1",
//             "description": "Section 1 description",
//             "order": 1,
//             "questions": [
//                 {"id": 1, "description": "Question 1", "type": "short-text", "required": true, choices: [], "order": 1, "value": ""},
//                 {"id": 2, "description": "Question 2", "type": "single-choice", "required": false, choices: [], "order": 2, "value": ""},
//             ]
//         },
//         {
//             "sectionId": 2,
//             "name": "Section 2",
//             "description": "This is section 2",
//             "order": 2,
//             "questions": [
//                 {"id": 3, "description": "What is 2+2?", "type": "short-text", "required": true, choices: [], "order": 1, "value": ""},
//                 {"id": 4, "description": "Upload your CV", "type": "file", "required": false, choices: [], "order": 3, "value": ""},
//                 {"id": 5, "description": "Choose an option", "type": "multi-choice", required: false, choices: ["One", "Two", "Three"], "order": 2, "value": ""}
//             ]
//         },
//     ]        
// }

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
    // return new Promise(function(resolve, reject) {
    //     setTimeout(() => resolve(dummyFormSpec), 1000);
    //   }).then(value => value);
}

function submit(response) {
    alert("Submitting form");
}