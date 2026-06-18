import axios from 'axios';
import { authHeader, extractErrorMessage } from '../base.service';

var baseUrl = process.env.REACT_APP_API_URL;

export var programmeService = {
  listSessions: listSessions,
  getSession: getSession,
  createSession: createSession,
  updateSession: updateSession,
  deleteSession: deleteSession,
  listSpeakers: listSpeakers,
  createSpeaker: createSpeaker,
  updateSpeaker: updateSpeaker,
  listSessionTypes: listSessionTypes,
  addSessionType: addSessionType,
  listTracks: listTracks,
  addTrack: addTrack,
};

function listSessions(eventId) {
  return axios
    .get(baseUrl + '/api/v1/programme/sessions?event_id=' + eventId, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function getSession(sessionId) {
  return axios
    .get(baseUrl + '/api/v1/programme/sessions/' + sessionId, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function createSession(payload) {
  return axios
    .post(baseUrl + '/api/v1/programme/sessions', payload, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function updateSession(sessionId, payload) {
  return axios
    .put(baseUrl + '/api/v1/programme/sessions/' + sessionId, payload, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function deleteSession(sessionId) {
  return axios
    .delete(baseUrl + '/api/v1/programme/sessions/' + sessionId, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function listSpeakers(eventId) {
  return axios
    .get(baseUrl + '/api/v1/programme/speakers?event_id=' + eventId, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function createSpeaker(payload) {
  return axios
    .post(baseUrl + '/api/v1/programme/speakers', payload, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function updateSpeaker(speakerId, payload) {
  return axios
    .put(baseUrl + '/api/v1/programme/speakers/' + speakerId, payload, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function listSessionTypes(eventId) {
  return axios
    .get(baseUrl + '/api/v1/programme/session-types?event_id=' + eventId, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function addSessionType(payload) {
  return axios
    .post(baseUrl + '/api/v1/programme/session-types', payload, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function listTracks(eventId) {
  return axios
    .get(baseUrl + '/api/v1/programme/tracks?event_id=' + eventId, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}

function addTrack(payload) {
  return axios
    .post(baseUrl + '/api/v1/programme/tracks', payload, {
      headers: authHeader(),
    })
    .then(function(response) {
      return { data: response.data, error: '' };
    })
    .catch(function(error) {
      return { data: null, error: extractErrorMessage(error) };
    });
}
