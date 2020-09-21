import React from 'react'

export function fetchQuestions() {
  return new Promise((resolve, reject) => {
    resolve([
      { "question_id": 1, "headline": "First question", "type": "short-text" },
      { "question_id": 2, "headline": "Second question", "type": "long-text" },
      { "question_id": 3, "headline": "Third question", "type": "multi-choice" },
      { "question_id": 4, "headline": "Forth question", "type": "file" },
      { "question_id": 5, "headline": "Fifth question", "type": "single-choice" }
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
          "start_date": "2020-06-01 [...]",    // ISO8601 format
          "is_submitted": true,
          "is_withdrawn": false,
          "submitted_date": "2020-06-03 [...]",  // ISO8601 format
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
          "start_date": "2020-06-01 [...]",    // ISO8601 format
          "is_submitted": true,
          "is_withdrawn": false,
          "submitted_date": "2020-06-03 [...]",  // ISO8601 format
          "language": "en",
          "reviewers": [
            { "reviewer_id": 63, "reviewer_name": "Mr Barack Obama", "review_response_id": 23 },
            null
          ],
          "answers": [
            { "question_id": 1, "headline": "First question", "value": "Hello world Hello world Hello world Hello worldHello world Hello world Hello world Hello world Hello world Hello world Hello world Hello world", "type": "long-text", "options": null },
            { "question_id": 3, "headline": "Third question", "value": "x-men", "type": "multi-choice", "options": [{ "label": "Harry Potter", "value": "harry-potter" }, { "label": "X-men", "value": "x-men" }] }
          ]
        },
        {
          "response_id": 3,
          "user_title": "Mr",
          "firstname": "Jo",
          "lastname": "Test",
          "start_date": "2020-06-01 [...]",    // ISO8601 format
          "is_submitted": true,
          "is_withdrawn": false,
          "submitted_date": "2020-06-03 [...]",  // ISO8601 format
          "language": "fr",
          "reviewers": [
            { "reviewer_id": 60, "reviewer_name": "Mr Justice Donner", "review_response_id": 44 },
            null
          ],
          "answers": [
            { "question_id": 4, "headline": "Forth question", "value": ["https://github.com/deep-learning-indaba/Baobab/issues/779", "Baobab"], "type": "file", "options": null },
            { "question_id": 3, "headline": "Third question", "value": "x-men", "type": "multi-choice", "options": [{ "label": "Harry Potter", "value": "harry-potter" }, { "label": "X-men", "value": "x-men" }] }
          ]
        }
      ]
    )
  })
}


