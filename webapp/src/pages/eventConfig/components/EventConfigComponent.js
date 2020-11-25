import React, { Component } from "react";
import { eventService } from "../../../services/events/events.service";
import { withRouter } from "react-router";
import DateTimePicker from "react-datetime-picker";
import Select from 'react-select';
import * as moment from 'moment';
import { withTranslation } from 'react-i18next';
import {
  TextField
} from '@material-ui/core';

 export class EventConfigComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      preEvent: this.emptyEvent,
      updatedEvent: this.emptyEvent,
      hasBeenUpdated: false,
      loading: true,
      error: ""
    };
  };



  componentDidMount() {
    if (this.props.event) {
      eventService.getEvent(this.props.event.id).then(result => {
        this.setState({
          loading: false,
          preEvent: result.event,
          updatedEvent: result.event,
          hasBeenUpdated: false,
          error: result.error
        });
      });
    };
  };



  onClickCancel = () => {
    this.setState({
      updatedEvent: this.state.preEvent,
      hasBeenUpdated: false
    });
  };



  onClickSubmit = () => {
    // PUT
    eventService.update(this.state.updatedEvent).then(result => {
      console.log(result)
      this.setState({
        preEvent: result.event,
        updatedEvent: result.event,
        hasBeenUpdated: false,
        error: Object.values(result.error)
      });
    });

  };


  handleDates = (fieldName, e) => {
    let formatDate = {
      target: {
        value: e.toISOString()
      }
    };
    this.updateEventDetails(fieldName, formatDate);
  };



  hasBeenEdited = () => {
    const { updatedEvent, preEvent } = this.state;
    const valdiate = updatedEvent !== preEvent;

    this.setState({
      hasBeenUpdated: valdiate ? true : false
    });
  };



  updateEventDetails = (fieldName, e, key) => {

    let u = {
      ...this.state.updatedEvent,
      // Some values are not nested, etsting against different values
      [fieldName]: key ? { [key]: e.target.value }
        :
        e.target ? e.target.value
          :
          e.value
    };

    this.setState({
      updatedEvent: u
    }, () => this.hasBeenEdited())
  };



  updateDateTimeEventDetails = (fieldName, value) => {
    let u = {
      ...this.state.updatedEvent,
      [fieldName]: value
    };

    this.setState({
      updatedEvent: u
    },
      () => this.hasBeenEdited()
    );
  };



  render() {
    const {
      loading,
      error,
      updatedEvent,
      preEvent,
      hasBeenUpdated
    } = this.state;

    const t = this.props.t;

    const loadingStyle = {
      width: "3rem",
      height: "3rem"
    };

    // Selector Options
    const options = {
      eventType: [
        { value: t('event'), label: 'event' },
        { value: t('award'), label: 'award' },
        { value: t('call'), label: 'call' }
      ],
      travelGrant: [
        { value: t("yes"), label: t("yes") },
        { value: t("no"), label: t("no") },
      ]
    };

    // format current date for MUI Time Picker
    const currentTime = () => {
      let date = moment().format('h:mm');
      return date.length == 4 ? String(date).padStart(5, '0') : date;
    };


    /* Loading */
    if (loading) {
      return (
        <div className="d-flex justify-content-center">
          <div className="spinner-border"
            style={loadingStyle}
            role="status">
            <span className="sr-only">Loading...</span>
          </div>
        </div>
      );
    };

    /* Error */
    if (error) {
      return <div className="alert alert-danger alert-container">
        {error}
      </div>;
    };


    return (
      <div className="event-config-wrapper">
        <div className="card">

          <form>

            <div className={"form-group row"}>

              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="organisation_id">
                {t("Organisation")}
              </label>

              {/* Organisation Name */}
              <div className="col-sm-10">
                <span
                  id="organisation_id"
                  class="badge badge-primary">{updatedEvent.organisation_name}</span>
                
              </div>
            </div>

            {/* Name */}
            <div className={"form-group row"}>
              <div className="d-flex w-100">
                <label className={"col-sm-2 col-form-label"} htmlFor="name">
                  {t("Event Name")}
                </label>
                <div className="w-100">
                  {preEvent &&
                    Object.keys(preEvent.name).map(val => {
                      return <div key={val} className="col-sm-12 mt-1">
                        <input
                          onChange={e => this.updateEventDetails("name", e, val)}
                          type="text"
                          className="form-control "
                          id="name"
                          placeholder={val}
                        />
                      </div>
                    })
                  }
                </div>
              </div>
            </div>

            {/* Description */}
            <div className={"form-group row"}>
              <div className="d-flex w-100">
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor="description">
                  {t("Description")}
                </label>
                <div className="w-100">
                  {preEvent &&
                    Object.keys(preEvent.description).map(val => {
                      return <div key={val} className="col-sm-12 mt-1">
                        <textarea
                          onChange={e => this.updateEventDetails("description", e, val)}
                          className="form-control"
                          id="description"
                          placeholder={val}
                        />
                      </div>
                    })
                  }
                </div>
              </div>
            </div>

            {/* Event Type */}
            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"}
                htmlFor="event-type">
                {t("Event Type")}
              </label>

              <div className="col-sm-10">
                <Select
                  onChange={e => this.updateEventDetails("event_type", e)}
                  options={options.eventType}
                />
              </div>
            </div>

            {/* Travel Grants */}
            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"}
                htmlFor="travel-grants">
                {t("Travel Grants")}
              </label>

              <div className="col-sm-10">
                <option disabled>{t('Does this event provide travel grants for participants')}</option>
                <Select
                  onChange={e => this.updateEventDetails("travel_grant", e)}
                  options={options.travelGrant}
                />
              </div>
            </div>

            {/* Miniconf Url */}
            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"}
                htmlFor="travel-grants">
                {t("MiniConf Url")}
              </label>

              <div className="col-sm-10">
                <textarea
                  className="w-100"
                  placeholder={t("If this is a virtual MiniConf event, enter the URL to the miniconf site")}
                  onChange={e => this.updateEventDetails("miniconf_url", e)}
                  className="form-control"
                  id="description"
                />
              </div>

            </div>

            {/* Key */}
            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"}
                htmlFor="key">
                {t("Key")}
              </label>

              <div className="col-sm-10">
              <span
                  id="key"
                  class="badge badge-primary">{updatedEvent.key}</span>
               
              </div>
            </div>

            {/* Email From */}
            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="email_from">
                {t("Email From")}
              </label>

              <div className="col-sm-10">
                <input
                  onChange={e => this.updateEventDetails("email_from", e)}
                  type="email"
                  className="form-control"
                  id="email_from"
                  value={updatedEvent.email_from} />
              </div>
            </div>

            {/* URL */}
            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"}
                htmlFor="url">
                {t("URL")}
              </label>
              <div className="col-sm-10">
                <input
                  onChange={e => this.updateEventDetails("url", e)}
                  type="text"
                  className="form-control"
                  id="url"
                  value={updatedEvent.url} />
              </div>
            </div>

            {/* Time */}
            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"}
                htmlFor="url">
                {t("Time")}
              </label>
              <div className="col-sm-10">
                <TextField
                   onChange={e => this.updateEventDetails("time", e)}
                  id="time"
                  label="Times are in UTC"
                  type="time"
                  defaultValue={currentTime()}
                  InputLabelProps={{
                    shrink: true,
                  }}
                  inputProps={{
                    step: 300, // 5 min
                  }}
                />


              </div>
            </div>

            <hr style={{ "marginTop": "50px" }}></hr>


            {/* Date Picker Section */}
            <div className="date-picker-section col-md-12">
              {/* Left Col */}
              <div className="first-col">

                {/*Item*/}
                <div className="date-item">
                  <p>{t('Date')}</p>
                  <div className="date-item-sections">
                    <div className="date-picker">
                      <label className={"col-form-label"} htmlFor="start_date">
                        {t("Start")}
                      </label>

                      <div>
                        <DateTimePicker
                          clearIcon={null}
                          disableClock={true}
                          onChange={e =>
                            this.handleDates("start_date", e)}
                          value={new Date(updatedEvent.start_date)} />
                      </div>
                    </div>

                    <div className="date-picker">
                      <label className={"col-form-label"} htmlFor="end_date">
                        {t("End Date")}
                      </label>

                      <div >
                        <DateTimePicker
                          clearIcon={null}
                          disableClock={true}
                          onChange={e => this.handleDates("end_date", e)}
                          value={new Date(updatedEvent.end_date)} />
                      </div>
                    </div>
                  </div>
                </div>

                {/*Item*/}
                <div className="date-item">
                  <p>{t('Application')}</p>
                  <div className="date-item-sections">

                    <div className="date-picker">
                      <label
                        className={"col-form-label"}
                        htmlFor="application_open">
                        {t("Open")}
                      </label>

                      <div >
                        <DateTimePicker
                          clearIcon={null}
                          disableClock={true}
                          onChange={e =>
                            this.handleDates("application_open", e)}
                          value={new Date(updatedEvent.application_open)} />
                      </div>
                    </div>
                    <div className="date-picker">
                      <label
                        className={" col-form-label"}
                        htmlFor="application_close"
                      >
                        {t("Close")}
                      </label>

                      <div >
                        <DateTimePicker
                          clearIcon={null}
                          disableClock={true}
                          onChange={e =>
                            this.handleDates("application_close", e)
                          }
                          value={new Date(updatedEvent.application_close)} />
                      </div>
                    </div>

                  </div>
                </div>

                {/*Item*/}
                <div className="date-item">
                  <p>{t('Review')}</p>
                  <div className="date-item-sections">

                    <div className="date-picker">
                      <label
                        className={"col-form-label"}
                        htmlFor="review_open">
                        {t("Open")}
                      </label>

                      <div >
                        <DateTimePicker
                          clearIcon={null}
                          disableClock={true}
                          onChange={e =>
                            this.handleDates("review_open", e)}
                          value={new Date(updatedEvent.review_open)} />
                      </div>
                    </div>
                    <div className="date-picker">
                      <label
                        className={"col-form-label"}
                        htmlFor="review_close">
                        {t("Close")}
                      </label>

                      <div >
                        <DateTimePicker
                          clearIcon={null}
                          disableClock={true}
                          onChange={e =>
                            this.handleDates("review_close", e)}
                          value={new Date(updatedEvent.review_close)} />
                      </div>
                    </div>

                  </div>
                </div>

              </div>



              {/* Right Col */}
              <div className="second-col">

                {/*Item*/}
                <div className="date-item">
                  <p>{t('Selection')}</p>
                  <div className="date-item-sections">

                    <div className="date-picker">
                      <label
                        className={"col-form-label"}
                        htmlFor="selection_open">
                        {t("Open")}
                      </label>

                      <div >
                        <DateTimePicker
                          clearIcon={null}
                          disableClock={true}
                          onChange={e =>
                            this.handleDates("selection_open", e)}
                          value={new Date(updatedEvent.selection_open)} />
                      </div>
                    </div>
                    <div className="date-picker">
                      <label
                        className={"col-form-label"}
                        htmlFor="selection_close">
                        {t("Close")}
                      </label>

                      <div >
                        <DateTimePicker
                          clearIcon={null}
                          disableClock={true}
                          onChange={e =>
                            this.handleDates("selection_close", e)}
                          value={new Date(updatedEvent.selection_close)} />
                      </div>
                    </div>

                  </div>
                </div>

                {/*Item*/}
                <div className="date-item">
                  <p>{t('Offer')}</p>
                  <div className="date-item-sections">

                    <div className="date-picker">
                      <label className={"col-form-label"} htmlFor="offer_open">
                        {t("Open")}
                      </label>

                      <div >
                        <DateTimePicker
                          clearIcon={null}
                          disableClock={true}
                          onChange={e =>
                            this.handleDates("offer_open", e)}
                          value={new Date(updatedEvent.offer_open)} />
                      </div>
                    </div>
                    <div className="date-picker">

                      <label
                        className={"col-form-label"}
                        htmlFor="offer_close">
                        {t("Close")}
                      </label>

                      <div >
                        <DateTimePicker
                          clearIcon={null}
                          disableClock={true}
                          onChange={e =>
                            this.handleDates("offer_close", e)}
                          value={new Date(updatedEvent.offer_close)} />
                      </div>
                    </div>

                  </div>
                </div>

                {/*Item*/}
                <div className="date-item">
                  <p>{t('Registration')}</p>
                  <div className="date-item-sections">

                    <div className="date-picker">
                      <label
                        className={"col-form-label"}
                        htmlFor="registration_open">
                        {t("Open")}
                      </label>

                      <div >
                        <DateTimePicker
                          clearIcon={null}
                          disableClock={true}
                          onChange={e =>
                            this.handleDates("registration_open", e)}
                          value={new Date(updatedEvent.registration_open)} />
                      </div>
                    </div>

                    <div className="date-picker">
                      <label
                        className={"col-form-label"}
                        htmlFor="registration_close">
                        {t("Close")}
                      </label>

                      <div >
                        <DateTimePicker
                          clearIcon={null}
                          disableClock={true}
                          onChange={e =>
                            this.handleDates("registration_close", e)}
                          value={new Date(updatedEvent.registration_close)}
                        />
                      </div>
                    </div>
                  </div>

                </div>
              </div>

              {/*
              
              */}

            </div>
          </form>

          <hr></hr>

          {/* Form Submittion and Cancel */}
          {hasBeenUpdated &&
            <div className={"form-group row submit"}>
              <div className={"col-sm-4"}>
                <button
                  className="btn btn-danger btn-lg btn-block"
                  onClick={() => this.onClickCancel()} >
                  {t("Cancel")}
                </button>
              </div>


              <div className={"col-sm-4"}>
                <button
                  onClick={() => this.onClickSubmit()}
                  className="btn btn-success btn-lg btn-block"
                  disabled={!hasBeenUpdated}
                >
                  {t("Update Event")}
                </button>
              </div>
            </div>
          }

        </div>
      </div>
    );
  }
}

export default withRouter(withTranslation()(EventConfigComponent));
