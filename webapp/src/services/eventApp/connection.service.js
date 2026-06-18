import axios from 'axios';
import { authHeader, extractErrorMessage } from '../base.service';

var baseUrl = process.env.REACT_APP_API_URL;

export var connectionService = {
  resolve: resolve,
  connect: connect,
  respond: respond,
  withdraw: withdraw,
  listConnections: listConnections,
  report: report,
};

function resolve(eventId, token) {
  return axios
    .get(baseUrl + '/api/v1/connection/resolve?event_id=' + eventId + '&t=' + encodeURIComponent(token), {
      headers: authHeader(),
    })
    .then(function(r) { return { data: r.data, error: null }; })
    .catch(function(e) { return { data: null, error: extractErrorMessage(e) }; });
}

function connect(eventId, toUserId) {
  return axios
    .post(baseUrl + '/api/v1/connection', { event_id: eventId, to_user_id: toUserId }, {
      headers: authHeader(),
    })
    .then(function(r) { return { data: r.data, error: null }; })
    .catch(function(e) { return { data: null, error: extractErrorMessage(e) }; });
}

function respond(eventId, fromUserId, action) {
  return axios
    .post(baseUrl + '/api/v1/connection/respond', { event_id: eventId, from_user_id: fromUserId, action: action }, {
      headers: authHeader(),
    })
    .then(function(r) { return { data: r.data, error: null }; })
    .catch(function(e) { return { data: null, error: extractErrorMessage(e) }; });
}

function withdraw(eventId, toUserId) {
  return axios
    .post(baseUrl + '/api/v1/connection/withdraw', { event_id: eventId, to_user_id: toUserId }, {
      headers: authHeader(),
    })
    .then(function(r) { return { data: r.data, error: null }; })
    .catch(function(e) { return { data: null, error: extractErrorMessage(e) }; });
}

function listConnections(eventId) {
  return axios
    .get(baseUrl + '/api/v1/connection/list?event_id=' + eventId, {
      headers: authHeader(),
    })
    .then(function(r) { return { data: r.data, error: null }; })
    .catch(function(e) { return { data: null, error: extractErrorMessage(e) }; });
}

function report(eventId, reportedUserId, reason) {
  return axios
    .post(baseUrl + '/api/v1/connection/report', {
      event_id: eventId, reported_user_id: reportedUserId, reason: reason,
    }, { headers: authHeader() })
    .then(function(r) { return { data: r.data, error: null }; })
    .catch(function(e) { return { data: null, error: extractErrorMessage(e) }; });
}
