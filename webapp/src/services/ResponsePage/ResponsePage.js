
const data = [
   { "id": 1,
    "application_form_id": 1,
    "user_id": 34,
    "is_submitted": true,
    "submitted_timestamp": "2020-06-02 [...]",    // ISO8601 Format
    "is_withdrawn": false,
    "withdrawn_timestamp": null,
    "started_timestamp": "2020-06-02 [...]",    // ISO8601 Format
    "user_title": "Ms",
    "firstname": "Jane",
    "lastname": "Bloggs",
    "answers": [
        { "id": 4, "question_id": 37, "value": "First answer" },
        { "id": 5, "question_id": 50, "value": "Second answer" },
        { "id": 6, "question_id": 44, "headline": "Third question", "value": [{"label": "Yes, transport only", "value": "Yes, transport only"}], "type": "multi-choice", "options": [{ "label": "Yes, transport only", "value": "Yes, transport only" }, { "label": "Yes, accommodation only", "value": "Yes, accommodation only" }] },
        { "id": 5, "question_id": 39, "headline": "Sixth question", "value": ["Chips", "Chocolate"], "type": "multi-file", "options": null }
        ],
    "language": "en"}
]

export function fetchResponse(param) {
    return new Promise((resolve, reject) => {
        data.forEach(val => {
            if (param.id == val.id) {
                resolve(val)
            }
        })
    })
}


