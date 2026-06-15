import axios from 'axios';
import { authHeader, extractErrorMessage } from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const profileService = {
  getMyProfile,
  updateMyProfile,
  viewProfile,
  listProfiles,
  getInterests,
  createInterest,
  getConsent,
  setConsent,
};

function getMyProfile(eventId) {
  return axios
    .get(baseUrl + '/api/v1/profile?event_id=' + eventId, { headers: authHeader() })
    .then(function(response) { return { data: response.data, error: '' }; })
    .catch(function(error) { return { data: null, error: extractErrorMessage(error) }; });
}

function updateMyProfile(payload) {
  return axios
    .put(baseUrl + '/api/v1/profile', payload, { headers: authHeader() })
    .then(function(response) { return { data: response.data, error: '' }; })
    .catch(function(error) { return { data: null, error: extractErrorMessage(error) }; });
}

function viewProfile(eventId, userId) {
  return axios
    .get(baseUrl + '/api/v1/profile/view?event_id=' + eventId + '&user_id=' + userId, { headers: authHeader() })
    .then(function(response) { return { data: response.data, error: '' }; })
    .catch(function(error) { return { data: null, error: extractErrorMessage(error) }; });
}

function listProfiles(eventId) {
  return axios
    .get(baseUrl + '/api/v1/profile/list?event_id=' + eventId, { headers: authHeader() })
    .then(function(response) { return { data: response.data, error: '' }; })
    .catch(function(error) { return { data: null, error: extractErrorMessage(error) }; });
}

function getInterests(eventId) {
  return axios
    .get(baseUrl + '/api/v1/profile/interests?event_id=' + eventId, { headers: authHeader() })
    .then(function(response) { return { data: response.data, error: '' }; })
    .catch(function(error) { return { data: null, error: extractErrorMessage(error) }; });
}

function createInterest(eventId, name) {
  return axios
    .post(baseUrl + '/api/v1/profile/interests', { event_id: eventId, name: name }, { headers: authHeader() })
    .then(function(response) { return { data: response.data, error: '' }; })
    .catch(function(error) { return { data: null, error: extractErrorMessage(error) }; });
}

function getConsent(eventId) {
  const url = eventId
    ? baseUrl + '/api/v1/consent?event_id=' + eventId
    : baseUrl + '/api/v1/consent';
  return axios
    .get(url, { headers: authHeader() })
    .then(function(response) { return { data: response.data, error: '' }; })
    .catch(function(error) { return { data: null, error: extractErrorMessage(error) }; });
}

function setConsent(payload) {
  return axios
    .post(baseUrl + '/api/v1/consent', payload, { headers: authHeader() })
    .then(function(response) { return { data: response.data, error: '' }; })
    .catch(function(error) { return { data: null, error: extractErrorMessage(error) }; });
}
