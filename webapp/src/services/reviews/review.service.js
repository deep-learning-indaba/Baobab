import axios from "axios";
import { authHeader, extractErrorMessage } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const reviewService = {
  getReviewForm,
  getReviewResponse,
  submit,
  getReviewAssignments,
  assignReviews,
  getReviewSummary,
  getReviewHistory,
  getReviewList,
  getResponseReview,
  assignResponsesToReviewer,
  deleteResponseReviewer,
  getReviewDetails,
  getReviewSummaryList,
  getReviewStage,
  getReviewFormDetails,
  updateReviewForm,
  createReviewForm
};

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

function getResponseReview(responseId, eventId) {
  return axios
    .get(baseUrl + `/api/v1/responsereview?response_id=${responseId}&event_id=${eventId}`, {
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

function submit(responseId, reviewFormId, scores, shouldUpdate, isSubmitted) {
  let review = {
    response_id: responseId,
    review_form_id: reviewFormId,
    scores: scores,
    is_submitted: isSubmitted
  };

  const promise = shouldUpdate 
      ? axios.put(baseUrl + "/api/v1/reviewresponse", review, { headers: authHeader() })
      : axios.post(baseUrl + "/api/v1/reviewresponse", review, { headers: authHeader() })
  
  return promise
    .then(function(response) {
      return {
        reviewResponse: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        reviewResponse: null,
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


function getReviewList(eventId) {
  return axios
    .get(
      baseUrl + "/api/v1/reviewlist?event_id=" + eventId,
      {
        headers: authHeader()
      }
    )
    .then(function(response) {
      return {
        reviewList: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        reviewList: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message
      };
    });
}

function assignResponsesToReviewer(eventId, responseIds, reviewerEmail) {
  const assignment = {
    event_id: eventId,
    response_ids: responseIds,
    reviewer_email: reviewerEmail
  };

  return axios
    .post(baseUrl + "/api/v1/assignresponsereviewer", assignment, {
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

function deleteResponseReviewer(eventId, responseId, reviewerUserId) {
  const deleteParams = {
    event_id: eventId,
    response_id: responseId,
    reviewer_user_id: reviewerUserId
  };

  return axios
    .delete(baseUrl + "/api/v1/assignresponsereviewer", {
      headers: authHeader(),
      params: deleteParams
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

function getReviewDetails(eventId) {
  return axios
    .get(
      baseUrl + "/api/v1/reviewresponsedetaillist?event_id=" + eventId,
      {
        headers: authHeader()
      }
    )
    .then(function(response) {
      return {
        reviewList: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        reviewList: null,
        error: extractErrorMessage(error)
      };
    });
}

function getReviewSummaryList(eventId) {
  return axios
    .get(
      baseUrl + "/api/v1/reviewresponsesummarylist?event_id=" + eventId,
      {
        headers: authHeader()
      }
    )
    .then(function(response) {
      return {
        reviewList: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        reviewList: null,
        error: extractErrorMessage(error)
      };
    });
}

function getReviewStage(eventId) {
  return axios
    .get(
      baseUrl + "/api/v1/reviewstage?event_id=" + eventId,
      {
        headers: authHeader()
      }
    )
    .then(function(response) {
      return {
        data: response.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        data: null,
        error: extractErrorMessage(error)
      };
    });
}

// function getReviewFormDetails(stage) {
//   return axios
//     .get(stage ? `https://60b8ab1bb54b0a0017c042c3.mockapi.io/api/v1/review-form-detail/${stage}`)
//     .then(function(res) {
//       return {
//         data: res.data,
//         error: ""
//       };
//     })
//     .catch(function(error) {
//       return {
//         data: null,
//         error: extractErrorMessage(error)
//       };
//     });
// }

function getReviewFormDetails(eventId,stage) {
  const url = stage
      ? `/api/v1/review-form-detail?event_id=${eventId}&stage=${stage}`
      : `/api/v1/review-form-detail?event_id=${eventId}`
  return axios
    .get(
      baseUrl + url,
      {
        headers: authHeader()
      }
    )
    .then(function(res) {
      return {
        data: res.data,
        error: ""
      };
    })
    .catch(function(error) {
      return {
        data: null,
        error: extractErrorMessage(error)
      };
    });
}

function updateReviewForm({
  id, eventId, isOpen, applicationFormId,
  stage, deadline, active, sectionsToSave
}) {
  const form = {
    "id": id,
    'event_id': eventId,
    "is_open": isOpen,
    "application_form_id": applicationFormId,
    "stage": stage,
    "deadline": deadline,
    "active": active,
    "sections": sectionsToSave
  }
  return axios
    .put(
      baseUrl + `/api/v1/review-form-detail`,
      form,
      {
        headers: authHeader()
      },
    )
    .then(res => {
      return {
        data: res.data,
        error: ""
      };
    })
    .catch(error => {
      return {
        data: null,
        error: extractErrorMessage(error)
      };
    });
}

function createReviewForm({
  eventId, isOpen, applicationFormId,
  stage, deadline, active, sectionsToSave
}) {
  const form = {
    'event_id': eventId,
    "is_open": isOpen,
    "application_form_id": applicationFormId,
    "stage": stage,
    "deadline": deadline,
    "active": active,
    "sections": sectionsToSave
  }
  return axios
  .post(
    baseUrl + '/api/v1/review-form-detail',
    form,
    {
      headers: authHeader()
    },
  )
    .then(res => {
      return {
        data: res.data,
        error: "",
        status: res.status
      };
    })
    .catch(error => {
      return {
        data: null,
        error: extractErrorMessage(error)
      };
    });
}