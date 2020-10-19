import React from 'react'

export function fetchQuestions() {
  return new Promise((resolve, reject) => {
    resolve([
      { "question_id": 1, "headline": "First question", "type": "short-text" },
      { "question_id": 2, "headline": "Second question", "type": "long-text" },
      { "question_id": 3, "headline": "Third question", "type": "multi-choice" },
      { "question_id": 4, "headline": "Forth question", "type": "file" },
      { "question_id": 5, "headline": "Fifth question", "type": "single-choice" },
      { "question_id": 6, "headline": "Sixth question", "type": "multi-file" }
    ])
  })
}

export function fetchResponse() {
  return new Promise((resolve, reject) => {
    resolve(
      [
        {
          "response_id": 1,
          "user_title": "Mr",
          "firstname": "Jimmy",
          "lastname": "Fallon",
          "start_date": "2020-06-01 T10:26:00.996Z",    // ISO8601 format
          "is_submitted": true,
          "is_withdrawn": false,
          "submitted_date": "2020-06-03 T10:26:00.996Z",  // ISO8601 format
          "language": "en",
          "reviewers": [
            { "reviewer_id": 23, "reviewer_name": "Mr James Dosh", "review_response_id": 33 },
            null
          ],
          "answers": [
            { "question_id": 1, "headline": "First question", "value": "Hello world", "type": "short-text", "options": null },
            { "question_id": 3, "headline": "Third question", "value": "harry-potter", "type": "multi-choice", "options": [{ "label": "Harry Potter", "value": "harry-potter" }, { "label": "X-men", "value": "x-men" }] }
          ]
        },
        {
          "response_id": 2,
          "user_title": "Ms",
          "firstname": "Halle",
          "lastname": "Berry",
          "start_date": "2020-06-01 T10:26:00.996Z",    // ISO8601 format
          "is_submitted": true,
          "is_withdrawn": false,
          "submitted_date": "2020-06-03 T10:26:00.996Z",  // ISO8601 format
          "language": "en",
          "reviewers": [
            { "reviewer_id": 63, "reviewer_name": "Mr Barack Obama", "review_response_id": 23 },
            null
          ],
          "answers": [
            { "question_id": 1, "headline": "First question", "value": "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur?", "type": "long-text", "options": null },
            { "question_id": 3, "headline": "Third question", "value": "x-men", "type": "multi-choice", "options": [{ "label": "Harry Potter", "value": "harry-potter" }, { "label": "X-men", "value": "x-men" }] }
          ]
        },
        {
          "response_id": 3,
          "user_title": "Mr",
          "firstname": "Jo",
          "lastname": "Test",
          "start_date": "2020-06-01 T10:26:00.996Z",    // ISO8601 format
          "is_submitted": true,
          "is_withdrawn": false,
          "submitted_date": "2020-06-03 T10:26:00.996Z",  // ISO8601 format
          "language": "fr",
          "reviewers": [
            { "reviewer_id": 60, "reviewer_name": "Mr Justice Donner", "review_response_id": 44 },
            null
          ],
          "answers": [
            { "question_id": 4, "headline": "Forth question", "value": "Tomatoes", "type": "file", "options": null },
            { "question_id": 3, "headline": "Third question", "value": "x-men", "type": "multi-choice", "options": [{ "label": "Harry Potter", "value": "harry-potter" }, { "label": "X-men", "value": "x-men" }] }
          ]
        },
        {
          "response_id": 4,
          "user_title": "Mr",
          "firstname": "Ares",
          "lastname": "Dares",
          "start_date": "2020-06-01 T10:26:00.996Z",    // ISO8601 format
          "is_submitted": true,
          "is_withdrawn": false,
          "submitted_date": "2020-06-03 T10:26:00.996Z",  // ISO8601 format
          "language": "fr",
          "reviewers": [
            { "reviewer_id": 35, "reviewer_name": "Mr Tempest", "review_response_id": 12 },
            null
          ],
          "answers": [
            { "question_id": 4, "headline": "Forth question", "value": "Baobab", "type": "file", "options": null },
            { "question_id": 6, "headline": "Sixth question", "value": ["Chips", "Chocolate"], "type": "multi-file", "options": null }
          ]
        }
      ]
    )
  })
}


