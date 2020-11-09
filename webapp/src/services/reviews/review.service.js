import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const reviewService = {
  getReviewForm,
  getReviewResponse,
  submit,
  getReviewAssignments,
  assignReviews,
  getReviewSummary,
  getReviewHistory,
  assignReviewer
};

function mock() {
  return [
    {
      "email": "avi@avi-net.co.za",
      "firstname": "Avishkar",
      "lastname": "Bhoopchand",
      "reviews_allocated": 1,
      "reviews_completed": 1,
      "user_title": "Mx"
  },
  {
      "email": "finn@avi-net.co.za",
      "firstname": "Finn",
      "lastname": "Dogg",
      "reviews_allocated": 0,
      "reviews_completed": 0,
      "user_title": "Mr"
  }
  ]
}

function assignReviewer() {
  return new Promise(resolve => {
    resolve({status: 201})
  })
}

function getReviewForm(eventId, skip) {
  return axios
    .get(baseUrl + "/api/v1/review?event_id=" + eventId + "&skip=" + skip, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        form: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        form: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function getReviewResponse(id) {
  return axios
    .get(baseUrl + "/api/v1/reviewresponse?id=" + id, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        form: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        form: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function submit(responseId, reviewFormId, scores, shouldUpdate) {
  let review = {
    response_id: responseId,
    review_form_id: reviewFormId,
    scores: scores
  };

  const promise = shouldUpdate 
      ? axios.put(baseUrl + "/api/v1/reviewresponse", review, { headers: authHeader() })
      : axios.post(baseUrl + "/api/v1/reviewresponse", review, { headers: authHeader() })
  
  return promise
    .then(function(response) {
      return {
        error: ""
      };
    })
    .catch(function(error) {
      return {
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function getReviewAssignments(eventId) {
  return axios
    .get(baseUrl + "/api/v1/reviewassignment?event_id=" + eventId, {
      headers: authHeader()
    
    })
    .then(function(response) {
      return {
        reviewers: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        reviewers: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function assignReviews(eventId, reviewerUserEmail, numReviews) {
  let assignment = {
    event_id: eventId,
    reviewer_user_email: reviewerUserEmail,
    num_reviews: numReviews
  };

  return axios
    .post(baseUrl + "/api/v1/reviewassignment", assignment, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        error: ""
      };
    })
    .catch(function(error) {
      return {
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function getReviewSummary(eventId) {
  return axios
    .get(baseUrl + "/api/v1/reviewassignment/summary?event_id=" + eventId, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        reviewSummary: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        reviewSummary: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function getReviewHistory(
  eventId,
  page_number,
  limit,
  sort_column = "submitted_timestamp"
) {
  return axios
    .get(
      baseUrl +
        "/api/v1/reviewhistory?event_id=" +
        eventId +
        "&page_number=" +
        page_number +
        "&limit=" +
        limit +
        "&sort_column=" +
        sort_column,
      {
        headers: authHeader()
      }
    )
    .then(function(response) {
      return {
        reviewHistory: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        reviewHistory: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}
