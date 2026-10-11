import axios from "axios";
import { authHeader, extractErrorMessage } from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

// A scope is where an edit applies: { eventId } for one event, or {} for the
// whole organisation (system admins only).
function root(scope) {
  return scope && scope.eventId
    ? `${baseUrl}/api/v1/events/${scope.eventId}`
    : `${baseUrl}/api/v1/organisation`;
}

function unwrap(promise) {
  return promise
    .then((response) => ({ data: response.data, error: "", errorDetail: null }))
    .catch((error) => ({
      data: null,
      error: extractErrorMessage(error),
      // { message, line, column, field } for a template that doesn't render.
      errorDetail: (error.response && error.response.data && error.response.data.error) || null,
      status: error.response && error.response.status,
    }));
}

function query(params) {
  const parts = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null)
    .map(([key, value]) => `${key}=${encodeURIComponent(value)}`);
  return parts.length ? `?${parts.join('&')}` : '';
}

function getEmailTypes(scope, uiLanguage) {
  return unwrap(axios.get(`${root(scope)}/email-types${query({ ui_language: uiLanguage })}`, { headers: authHeader() }));
}

function getEmailType(scope, key, uiLanguage) {
  return unwrap(axios.get(`${root(scope)}/email-types/${key}${query({ ui_language: uiLanguage })}`, { headers: authHeader() }));
}

function getTemplate(scope, key, language) {
  return unwrap(axios.get(`${root(scope)}/email-templates/${key}${query({ language })}`, { headers: authHeader() }));
}

function saveTemplate(scope, key, language, subject, body) {
  return unwrap(axios.put(`${root(scope)}/email-templates/${key}${query({ language })}`,
    { subject, body }, { headers: authHeader() }));
}

function resetTemplate(scope, key, language) {
  return unwrap(axios.delete(`${root(scope)}/email-templates/${key}${query({ language })}`, { headers: authHeader() }));
}

function getRevisions(scope, key, language) {
  return unwrap(axios.get(`${root(scope)}/email-templates/${key}/revisions${query({ language })}`, { headers: authHeader() }));
}

function previewTemplate(scope, key, data) {
  return unwrap(axios.post(`${root(scope)}/email-templates/${key}/preview`, data, { headers: authHeader() }));
}

function testSend(scope, key, data) {
  return unwrap(axios.post(`${root(scope)}/email-templates/${key}/test-send`, data, { headers: authHeader() }));
}

function translateTemplate(scope, key, language, sourceLanguage) {
  return unwrap(axios.post(`${root(scope)}/email-templates/${key}/translate${query({ language })}`,
    { source_language: sourceLanguage }, { headers: authHeader() }));
}

function getLayout(scope, language) {
  return unwrap(axios.get(`${root(scope)}/email-layout${query({ language })}`, { headers: authHeader() }));
}

function saveLayout(scope, language, layout) {
  return unwrap(axios.put(`${root(scope)}/email-layout${query({ language })}`, layout, { headers: authHeader() }));
}

function previewLayout(scope, language, layout) {
  return unwrap(axios.post(`${root(scope)}/email-layout/preview`, { ...layout, language }, { headers: authHeader() }));
}

export const emailTemplatesService = {
  getEmailTypes,
  getEmailType,
  getTemplate,
  saveTemplate,
  resetTemplate,
  getRevisions,
  previewTemplate,
  testSend,
  translateTemplate,
  getLayout,
  saveLayout,
  previewLayout,
};
