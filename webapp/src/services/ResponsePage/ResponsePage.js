import React from 'react'

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
        { "id": 4, "question_id": 1, "value": "First answer" },
        { "id": 5, "question_id": 2, "value": "Second answer" }
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


