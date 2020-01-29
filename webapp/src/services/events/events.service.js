import axios from "axios";
import { authHeader } from "../base.service";

const baseUrl = process.env.REACT_APP_API_URL;

export const eventsService = {
  getEvents,
  create,
  update
};

export function getEvents() {
  return axios
    .get(baseUrl + `/api/v1/events`, { headers: authHeader() })
    .then(function(response) {
      // handle success
      return { events: response.data, error: "" };
    })
    .catch(function(error) {
      // handle error
      return { events: [], error: error };
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
        registration_close: event.registration_close
      },
      { headers: authHeader() }
    )
    .then(response => {
      // handle success
      let event = null;
      if (response) {
        event = response.data;
      }
      return { event: event, error: "" };
    })
    .catch(error => {
      // handle error
      return { event: null, error: error };
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
        registration_close: event.registration_close
      },
      { headers: authHeader() }
    )
    .then(response => {
      // handle success
      let event = null;
      if (response) {
        event = response.data;
      }
      return { event: event, error: "" };
    })
    .catch(error => {
      // handle error
      return { event: null, error: error };
    });
}
