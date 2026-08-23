import axios from "axios";
import { authHeader, extractErrorMessage } from '../base.service';

const baseUrl = process.env.REACT_APP_API_URL;

export const documentsService = {
  getTemplates,
  getTemplate,
  createTemplate,
  updateTemplate,
  deleteTemplate,
  addVariant,
  updateVariant,
  deleteVariant,
  setFormLinks,
  validateSource,
  analyseTemplate,
  previewTemplate,
  generateDocument,
  getGeneratedDocuments,
  downloadDocument,
  getAvailableDocuments,
  requestDocument,
  getUserEventData,
  setUserEventData,
};

function unwrap(promise) {
  return promise
    .then((response) => ({ data: response.data, error: "" }))
    .catch((error) => ({ data: null, error: extractErrorMessage(error), status: error.response && error.response.status }));
}

function getTemplates(eventId) {
  return unwrap(axios.get(`${baseUrl}/api/v1/documents/templates?event_id=${eventId}`, { headers: authHeader() }));
}

function getTemplate(templateId) {
  return unwrap(axios.get(`${baseUrl}/api/v1/documents/templates/${templateId}`, { headers: authHeader() }));
}

function createTemplate(eventId, data) {
  return unwrap(axios.post(`${baseUrl}/api/v1/documents/templates?event_id=${eventId}`, data, { headers: authHeader() }));
}

function updateTemplate(templateId, data) {
  return unwrap(axios.put(`${baseUrl}/api/v1/documents/templates/${templateId}`, data, { headers: authHeader() }));
}

function deleteTemplate(templateId) {
  return unwrap(axios.delete(`${baseUrl}/api/v1/documents/templates/${templateId}`, { headers: authHeader() }));
}

function addVariant(templateId, data) {
  return unwrap(axios.post(`${baseUrl}/api/v1/documents/templates/${templateId}/variants`, data, { headers: authHeader() }));
}

function updateVariant(templateId, variantId, data) {
  return unwrap(axios.put(`${baseUrl}/api/v1/documents/templates/${templateId}/variants/${variantId}`, data, { headers: authHeader() }));
}

function deleteVariant(templateId, variantId) {
  return unwrap(axios.delete(`${baseUrl}/api/v1/documents/templates/${templateId}/variants/${variantId}`, { headers: authHeader() }));
}

function setFormLinks(templateId, formLinks) {
  return unwrap(axios.put(`${baseUrl}/api/v1/documents/templates/${templateId}/forms`, { form_links: formLinks }, { headers: authHeader() }));
}

function validateSource(eventId, url) {
  return unwrap(axios.post(`${baseUrl}/api/v1/documents/validate-source?event_id=${eventId}`, { url }, { headers: authHeader() }));
}

function analyseTemplate(templateId) {
  return unwrap(axios.post(`${baseUrl}/api/v1/documents/templates/${templateId}/analyse`, {}, { headers: authHeader() }));
}

function previewTemplate(templateId, userId, language = 'en') {
  return unwrap(axios.post(`${baseUrl}/api/v1/documents/templates/${templateId}/preview`, { user_id: userId, language }, { headers: authHeader() }));
}

function generateDocument(templateId, userId, options = {}) {
  return unwrap(axios.post(`${baseUrl}/api/v1/documents/generate`, {
    template_id: templateId, user_id: userId, ...options,
  }, { headers: authHeader() }));
}

function getGeneratedDocuments(eventId, templateId) {
  const params = new URLSearchParams({ event_id: eventId });
  if (templateId) params.append('template_id', templateId);
  return unwrap(axios.get(`${baseUrl}/api/v1/documents/generated?${params.toString()}`, { headers: authHeader() }));
}

function downloadDocument(documentId, filename) {
  // A plain <a href> can't carry the Authorization header the endpoint
  // requires, so the PDF is fetched as a blob and "downloaded" by clicking a
  // throwaway link pointed at an object URL instead.
  return axios
    .get(`${baseUrl}/api/v1/documents/generated/${documentId}/download`, {
      headers: authHeader(),
      responseType: 'blob',
    })
    .then((response) => {
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename || 'document.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      return { error: "" };
    })
    .catch((error) => ({ error: extractErrorMessage(error) }));
}

function getAvailableDocuments(eventId) {
  return unwrap(axios.get(`${baseUrl}/api/v1/documents/available?event_id=${eventId}`, { headers: authHeader() }));
}

function requestDocument(templateId) {
  return unwrap(axios.post(`${baseUrl}/api/v1/documents/request`, { template_id: templateId }, { headers: authHeader() }));
}

function getUserEventData(eventId) {
  return unwrap(axios.get(`${baseUrl}/api/v1/events/${eventId}/user-data`, { headers: authHeader() }));
}

function setUserEventData(eventId, entries) {
  return unwrap(axios.put(`${baseUrl}/api/v1/events/${eventId}/user-data`, { entries }, { headers: authHeader() }));
}
