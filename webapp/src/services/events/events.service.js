import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const eventService = {
  getEvent,
  create,
  update,
  getEvents,
  getByKey,
  getEventRoles,
  deleteEventRole,
  addEventRole,
  getResourceLinks,
  createResourceLink,
  updateResourceLink,
  deleteResourceLink
};

export function getEvent(event_id) {
  return axios
    .get(baseUrl + `/api/v1/event?id=` + event_id + "&cache_bust=1", { headers: authHeader() })
    .then(response => {
      return {
        event: response.data,
        error: "",
        statusCode: response.status
      };
    })
    .catch(error => {
      return {
        event: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
        statusCode: error.response && error.response.status
      };
    });
}

export function create(event) {
  return axios
    .post(
      baseUrl + `/api/v1/event`,
      {
        name: event.name,
        description: event.description,
        start_date: event.start_date,
        end_date: event.end_date,
        key: event.key,
        organisation_id: event.organisation_id,
        email_from: event.email_from,
        url: event.url,
        application_open: event.application_open,
        application_close: event.application_close,
        review_open: event.review_open,
        review_close: event.review_close,
        selection_open: event.selection_open,
        selection_close: event.selection_close,
        offer_open: event.offer_open,
        offer_close: event.offer_close,
        registration_open: event.registration_open,
        registration_close: event.registration_close,
        event_type: event.event_type,
        travel_grant: event.travel_grant,
        miniconf_url: event.miniconf_url,
        contact_email: event.contact_email,
        image: event.image,
        timezone: event.timezone,
        checkin_mode: event.checkin_mode
      },
      { headers: authHeader() }
    )
    .then(response => {
      return {
        event: response.data,
        error: "",
        statusCode: response.status
      };
    })
    .catch(error => {
      return {
        event: event,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
        statusCode: error.response && error.response.status
      };
    });
}

export function update(event) {
  return axios
    .put(
      baseUrl + `/api/v1/event`,
      {
        id: event.id,
        name: event.name,
        description: event.description,
        start_date: event.start_date,
        end_date: event.end_date,
        key: event.key,
        organisation_id: event.organisation_id,
        email_from: event.email_from,
        url: event.url,
        application_open: event.application_open,
        application_close: event.application_close,
        review_open: event.review_open,
        review_close: event.review_close,
        selection_open: event.selection_open,
        selection_close: event.selection_close,
        offer_open: event.offer_open,
        offer_close: event.offer_close,
        registration_open: event.registration_open,
        registration_close: event.registration_close,
        event_type: event.event_type,
        travel_grant: event.travel_grant,
        miniconf_url: event.miniconf_url,
        contact_email: event.contact_email,
        image: event.image,
        timezone: event.timezone,
        checkin_mode: event.checkin_mode
      },
      { headers: authHeader() }
    )
    .then(response => {
      return {
        event: response.data,
        error: "",
        statusCode: response.status
      };
    })
    .catch(error => {
      return {
        event: event,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
        statusCode: error.response && error.response.status
      };
    });
}

function getEvents() {
  return axios
    .get(baseUrl + `/api/v1/events?cache_bust=1`, { headers: authHeader() })
    .then(function(response) {
      return {
        events: response.data,
        error: "",
        statusCode: response.status
      };
    })
    .catch(function(error) {
      return {
        events: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
        statusCode: error.response && error.response.status
      };
    });
}

function getByKey(event_key) {
  return axios
    .get(baseUrl + `/api/v1/event-by-key?event_key=${event_key}&cache_bust=1`, {
      headers: authHeader()
    })
    .then(function(response) {
      return {
        event: response.data,
        error: "",
        statusCode: response.status
      };
    })
    .catch(function(error) {
      return {
        event: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
        statusCode: error.response && error.response.status
      };
    });
}

function getEventRoles(event_id) {
  return axios.get(baseUrl + `/api/v1/event-roles?event_id=${event_id}`, { headers: authHeader() })
    .then(response => {
      return {
        eventRoles: response.data,
        error: "",
        statusCode: response.status
      };
    })
    .catch(error => {
      return {
        eventRoles: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
        statusCode: error.response && error.response.status
      };
    });
}

function deleteEventRole(event_id, event_role_id) {
  return axios.delete(baseUrl + `/api/v1/event-roles?event_id=${event_id}&event_role_id=${event_role_id}`, { headers: authHeader() })
    .then(response => {
      return {
        eventRoles: response.data,
        error: "",  
        statusCode: response.status
      };
    })
    .catch(error => {
      return {
        eventRoles: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
        statusCode: error.response && error.response.status
      };
    });
}

function addEventRole(event_id, email, role) {
  const data = {
    event_id: event_id,
    email: email,
    role: role
  };

  return axios.post(baseUrl + `/api/v1/event-roles`, data, { headers: authHeader() })
    .then(response => {
      return {
        eventRoles: response.data,
        error: "",  
        statusCode: response.status
      };
    })
    .catch(error => {
      return {
        eventRoles: null,
        error:
          error.response && error.response.data
            ? error.response.data.message
            : error.message,
        statusCode: error.response && error.response.status
      };
    });
}

function getResourceLinks(event_id, language) {
  const lang = language || 'en';
  return axios
    .get(baseUrl + `/api/v1/event-resource-links?event_id=${event_id}&language=${lang}`, { headers: authHeader() })
    .then(response => ({ links: response.data, error: '' }))
    .catch(error => ({
      links: [],
      error: error.response && error.response.data ? error.response.data.message : error.message
    }));
}

function createResourceLink(link) {
  return axios
    .post(baseUrl + '/api/v1/event-resource-links', link, { headers: authHeader() })
    .then(response => ({ link: response.data, error: '' }))
    .catch(error => ({
      link: null,
      error: error.response && error.response.data ? error.response.data.message : error.message
    }));
}

function updateResourceLink(link) {
  return axios
    .put(baseUrl + '/api/v1/event-resource-links', link, { headers: authHeader() })
    .then(response => ({ link: response.data, error: '' }))
    .catch(error => ({
      link: null,
      error: error.response && error.response.data ? error.response.data.message : error.message
    }));
}

function deleteResourceLink(event_id, id) {
  return axios
    .delete(baseUrl + `/api/v1/event-resource-links?event_id=${event_id}&id=${id}`, { headers: authHeader() })
    .then(response => ({ error: '' }))
    .catch(error => ({
      error: error.response && error.response.data ? error.response.data.message : error.message
    }));
}
