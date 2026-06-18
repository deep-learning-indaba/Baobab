import axios from 'axios';
import { authHeader, extractErrorMessage } from '../base.service';

var baseUrl = process.env.REACT_APP_API_URL;

export var announcementService = {
  listInbox: listInbox,
  listActive: listActive,
  listAdmin: listAdmin,
  getAnnouncement: getAnnouncement,
  create: create,
  remove: remove,
  subscribePush: subscribePush,
  unsubscribePush: unsubscribePush,
};

function listInbox(eventId, language) {
  return axios
    .get(baseUrl + '/api/v1/announcement?event_id=' + eventId + '&language=' + (language || 'en'), {
      headers: authHeader(),
    })
    .then(function(r) { return { data: r.data, error: '' }; })
    .catch(function(e) { return { data: null, error: extractErrorMessage(e) }; });
}

function listActive(eventId, language) {
  return axios
    .get(baseUrl + '/api/v1/announcement/active?event_id=' + eventId + '&language=' + (language || 'en'))
    .then(function(r) { return { data: r.data, error: '' }; })
    .catch(function(e) { return { data: null, error: extractErrorMessage(e) }; });
}

function listAdmin(eventId, language) {
  return axios
    .get(baseUrl + '/api/v1/announcement/admin?event_id=' + eventId + '&language=' + (language || 'en'), {
      headers: authHeader(),
    })
    .then(function(r) { return { data: r.data, error: '' }; })
    .catch(function(e) { return { data: null, error: extractErrorMessage(e) }; });
}

function getAnnouncement(eventId, announcementId, language) {
  return axios
    .get(baseUrl + '/api/v1/announcement/' + announcementId + '?event_id=' + eventId + '&language=' + (language || 'en'), {
      headers: authHeader(),
    })
    .then(function(r) { return { data: r.data, error: '' }; })
    .catch(function(e) { return { data: null, error: extractErrorMessage(e) }; });
}

function create(payload) {
  return axios
    .post(baseUrl + '/api/v1/announcement', payload, { headers: authHeader() })
    .then(function(r) { return { data: r.data, error: '' }; })
    .catch(function(e) { return { data: null, error: extractErrorMessage(e) }; });
}

function remove(announcementId, eventId) {
  return axios
    .delete(baseUrl + '/api/v1/announcement/' + announcementId + '?event_id=' + eventId, {
      headers: authHeader(),
    })
    .then(function(r) { return { data: r.data, error: '' }; })
    .catch(function(e) { return { data: null, error: extractErrorMessage(e) }; });
}

function subscribePush(subscription) {
  var sub = subscription.toJSON ? subscription.toJSON() : subscription;
  return axios
    .post(baseUrl + '/api/v1/push-subscription', {
      endpoint: sub.endpoint,
      keys: sub.keys,
      user_agent: navigator.userAgent,
    }, { headers: authHeader() })
    .then(function(r) { return { data: r.data, error: '' }; })
    .catch(function(e) { return { data: null, error: extractErrorMessage(e) }; });
}

function unsubscribePush(endpoint) {
  return axios
    .delete(baseUrl + '/api/v1/push-subscription', {
      headers: authHeader(),
      data: { endpoint: endpoint },
    })
    .then(function(r) { return { data: r.data, error: '' }; })
    .catch(function(e) { return { data: null, error: extractErrorMessage(e) }; });
}
