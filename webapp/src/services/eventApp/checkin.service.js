import axios from 'axios';
import { authHeader, extractErrorMessage } from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const checkinService = {
  getMyTicket,
  resolveToken,
  checkin,
  getBadgeExport,
  markBadgesExported,
  getBlankBadges,
  linkBadge,
};

function getMyTicket(eventId) {
  return axios
    .get(baseUrl + '/api/v1/my-ticket?event_id=' + eventId, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function resolveToken(eventId, token) {
  return axios
    .get(baseUrl + '/api/v1/checkin/resolve?event_id=' + eventId + '&t=' + encodeURIComponent(token), {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function checkin(params) {
  const body = { event_id: params.eventId, token: params.token };
  return axios
    .post(baseUrl + '/api/v1/checkin', body, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '', statusCode: response.status };
    })
    .catch(function(error) {
      return {
        data: null,
        error: extractErrorMessage(error),
        statusCode: error.response && error.response.status,
      };
    });
}

function markBadgesExported(eventId, userIds) {
  return axios
    .post(baseUrl + '/api/v1/checkin/badge-export', { event_id: eventId, user_ids: userIds }, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function getBadgeExport(eventId) {
  return axios
    .get(baseUrl + '/api/v1/checkin/badge-export?event_id=' + eventId, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function getBlankBadges(eventId, count) {
  return axios
    .get(baseUrl + '/api/v1/checkin/blank-badges?event_id=' + eventId + '&count=' + count, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function linkBadge(eventId, userId, token) {
  return axios
    .post(baseUrl + '/api/v1/checkin/link-badge', { event_id: eventId, user_id: userId, token: token }, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '', statusCode: response.status };
    })
    .catch(function(error) {
      return {
        data: null,
        error: extractErrorMessage(error),
        statusCode: error.response && error.response.status,
      };
    });
}
