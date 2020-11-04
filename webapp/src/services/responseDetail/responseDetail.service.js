
export const response = {
    list,
    del,
    post
};

function list() {
    return new Promise(resolve => {
    resolve({
        "id": 1, 
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
          {"id": 4, "question_id": 1, "value": "First answer"},
          {"id": 5, "question_id": 2, "value": "Second answer"}
        ],
        "language": "en",
        "tags": [
            {"id": 5, "headline": "éducation"},
            {"id": 7, "headline": "soins de santé"}
         ],
         "reviewers": [ 
              {"reviewer_user_id": 4, "user_title": "Mr", "firstname": "Joe", "lastname": "Soap", "completed": false},
              null
          ]
      })
})
};

function del() {
    return new Promise(resolve => {
    resolve()
})
};

function post() {
    return new Promise(resolve => {
    resolve()
})
};