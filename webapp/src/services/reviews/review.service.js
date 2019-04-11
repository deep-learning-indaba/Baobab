import axios from 'axios';
import {authHeader} from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const reviewService = {
    getReviewForm,
    submit,
    getReviewAssignments,
    assignReviews
}

function getReviewForm(eventId, skip) {
    return axios
        .get(baseUrl + "/api/v1/review?event_id=" + eventId + "&skip=" + skip, { 'headers': authHeader() })
        .then(function(response) {
            return {
                form: response.data,
                error: ""
            };
        })
        .catch(function(error) {
            return {
                form: null,
                error: (error.response && error.response.data) ? error.response.data.message : error.message
            };
        });
}

function submit(responseId, reviewFormId, scores) {
    let review = {
        "response_id": responseId,
        "review_form_id": reviewFormId,
        "scores": scores
      };

    return axios
        .post(baseUrl + "/api/v1/reviewresponse", review, { 'headers': authHeader() })
        .then(function(response) {
            return {
                error: ""
            }
        })
        .catch(function(error) {
            return {
                error: (error.response && error.response.data) ? error.response.data.message : error.message
            };
        });
}

function getReviewAssignments(eventId) {
    return axios
        .get(baseUrl + "/api/v1/reviewassignment?event_id=" + eventId, { 'headers': authHeader() })
        .then(function(response) {
            return {
                reviewers: response.data,
                error: ""
            };
        })
        .catch(function(error) {
            return {
                reviewers: null,
                error: (error.response && error.response.data) ? error.response.data.message : error.message
            };
        });    
}

function assignReviews(eventId, reviewers) {
	Promise.all(reviewers.map(review => assignReview(eventId, review.email, review.numNewReviews)))
	.then(function(response) {
		return {
			error: ""
		}
	})
	.catch(function(error) {
		//TODO: This probably won't work as expected with Promise.all
		return {
			error: (error.response && error.response.data) ? error.response.data.message : error.message
		};
	});
}

function assignReview(eventId, reviewerUserEmail, numReviews) {
    let assignment = {
        "event_id": eventId,
        "reviewer_user_email": reviewerUserEmail,
        "num_reviews": numReviews
    };

    return axios
        .post(baseUrl + "/api/v1/reviewassignment", assignment, { 'headers': authHeader() })
        .then(function(response) {
            return {
                error: ""
            }
        })
        .catch(function(error) {
            return {
                error: (error.response && error.response.data) ? error.response.data.message : error.message
            };
        });    
}