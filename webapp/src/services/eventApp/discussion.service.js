import axios from 'axios';
import { authHeader, extractErrorMessage } from '../base.service';

var baseUrl = process.env.REACT_APP_API_URL;

function ok(r) { return { data: r.data, error: '' }; }
function fail(e) { return { data: null, error: extractErrorMessage(e) }; }

export var discussionService = {
  listSpaces: function (eventId) {
    return axios.get(baseUrl + '/api/v1/discussion/space?event_id=' + eventId, { headers: authHeader() }).then(ok).catch(fail);
  },
  getSpace: function (eventId, spaceId) {
    return axios.get(baseUrl + '/api/v1/discussion/space/' + spaceId + '?event_id=' + eventId, { headers: authHeader() }).then(ok).catch(fail);
  },
  createSpace: function (eventId, name, description, subscribeOnReply) {
    return axios.post(baseUrl + '/api/v1/discussion/space', { event_id: eventId, name: name, description: description, subscribe_on_reply: subscribeOnReply }, { headers: authHeader() }).then(ok).catch(fail);
  },
  updateSpace: function (eventId, spaceId, fields) {
    return axios.put(baseUrl + '/api/v1/discussion/space/' + spaceId, Object.assign({ event_id: eventId }, fields), { headers: authHeader() }).then(ok).catch(fail);
  },
  deleteSpace: function (eventId, spaceId) {
    return axios.delete(baseUrl + '/api/v1/discussion/space/' + spaceId + '?event_id=' + eventId, { headers: authHeader() }).then(ok).catch(fail);
  },
  listThreads: function (eventId, spaceId) {
    return axios.get(baseUrl + '/api/v1/discussion/thread?event_id=' + eventId + '&space_id=' + spaceId, { headers: authHeader() }).then(ok).catch(fail);
  },
  getThread: function (eventId, threadId) {
    return axios.get(baseUrl + '/api/v1/discussion/thread/' + threadId + '?event_id=' + eventId, { headers: authHeader() }).then(ok).catch(fail);
  },
  createThread: function (eventId, spaceId, subject, bodyMarkdown) {
    return axios.post(baseUrl + '/api/v1/discussion/thread', { event_id: eventId, space_id: spaceId, subject: subject, body_markdown: bodyMarkdown }, { headers: authHeader() }).then(ok).catch(fail);
  },
  reply: function (eventId, threadId, bodyMarkdown) {
    return axios.post(baseUrl + '/api/v1/discussion/thread/' + threadId + '/reply', { event_id: eventId, body_markdown: bodyMarkdown }, { headers: authHeader() }).then(ok).catch(fail);
  },
  editMessage: function (eventId, messageId, bodyMarkdown) {
    return axios.put(baseUrl + '/api/v1/discussion/message/' + messageId, { event_id: eventId, body_markdown: bodyMarkdown }, { headers: authHeader() }).then(ok).catch(fail);
  },
  deleteMessage: function (eventId, messageId, reason) {
    return axios.delete(baseUrl + '/api/v1/discussion/message/' + messageId + '?event_id=' + eventId + (reason ? '&reason=' + encodeURIComponent(reason) : ''), { headers: authHeader() }).then(ok).catch(fail);
  },
  reportMessage: function (eventId, messageId, reason) {
    return axios.post(baseUrl + '/api/v1/discussion/message/' + messageId + '/report', { event_id: eventId, reason: reason }, { headers: authHeader() }).then(ok).catch(fail);
  },
  setSubscription: function (eventId, threadId, subscribed) {
    return axios.post(baseUrl + '/api/v1/discussion/thread/' + threadId + '/subscription', { event_id: eventId, subscribed: subscribed }, { headers: authHeader() }).then(ok).catch(fail);
  },
  listSubscriptions: function (eventId) {
    return axios.get(baseUrl + '/api/v1/discussion/subscription?event_id=' + eventId, { headers: authHeader() }).then(ok).catch(fail);
  },
  listReports: function (eventId) {
    return axios.get(baseUrl + '/api/v1/discussion/report?event_id=' + eventId, { headers: authHeader() }).then(ok).catch(fail);
  },
  dismissReport: function (eventId, reportId) {
    return axios.post(baseUrl + '/api/v1/discussion/report/' + reportId + '/dismiss', { event_id: eventId }, { headers: authHeader() }).then(ok).catch(fail);
  },
};
