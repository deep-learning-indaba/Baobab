import React, { Component } from "react";
import CreateComponent from './CreateComponent';
import { eventService } from "../../../services/events/events.service";
import { withRouter } from "react-router";
import DateTimePicker from "react-datetime-picker";
import Select from 'react-select';
import * as moment from 'moment';
import { withTranslation } from 'react-i18next';
import {
  TextField,
  Button
} from '@material-ui/core';

export class EventConfigComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      preEvent: this.emptyEvent,
      updatedEvent: this.emptyEvent,
      hasBeenUpdated: false,
      updatedNewEvent: this.emptyEvent,
      loading: true,
      error: "",
      fileUpload: null,
      file: null
    };
  };


  // Populate State
  componentDidMount() {
    // Edit Event
    if (this.props.event) {
      eventService.getEvent(this.props.event.id).then(result => {
        this.setState({
          loading: false,
          preEvent: result.event,
          updatedEvent: this.props.history.location.state ? this.props.history.location.state : result.event,
          hasBeenUpdated: false,
          error: result.error
        });
      });
    }
    // Create Event
    else {
      let eventDetails = {
        organistation_id: this.props.organisation.id,
        start_date: new Date(),
        end_date: new Date(),
        application_open: new Date(),
        application_close: new Date(),
        review_open: new Date(),
        review_close: new Date(),
        selection_open: new Date(),
        selection_close: new Date(),
        offer_open: new Date(),
        offer_close: new Date(),
        registration_open: new Date(),
        registration_close: new Date(),
      };

      this.setState({
        loading: false,
        preNewEvent: eventDetails,
        updatedNewEvent: this.props.history.location.state ? this.props.history.location.state : eventDetails

      });
    };
  };


  // on Click Cancel
  onClickCancel = () => {
    this.setState({
      updatedEvent: this.state.preEvent,
      hasBeenUpdated: false
    });
  };


  // on Click Submit
  submitEvent = () => {
    // PUT
    eventService.update(this.state.updatedEvent).then(result => {
      console.log(result)
      this.setState({
        preEvent: result.event,
        updatedEvent: result.event,
        hasBeenUpdated: false,
      });
    }).catch(result => {
      this.setState({
        error: result.statusCode
      });
    });
  };


  createEvent = () => {
    // Create
    eventService.create(this.state.updatedNewEvent).then(result => {
      console.log(result)
      this.setState({
        preEvent: result.event,
        updatedEvent: result.event,
        hasBeenUpdated: false,
        error: Object.values(result.error)
      });
    });
  };


  // Handle Date Selectors
  handleDates = (fieldName, e) => {
    let formatDate = e.toISOString();
    formatDate = formatDate.substring(0, formatDate.length - 5) + "Z";

    let dateObj = {
      target: {
        value: formatDate
      }
    };

    this.state.preEvent ?
      this.updateEventDetails(fieldName, dateObj) : this.createEventDetails(fieldName, dateObj)
  };


  // Handle Upload
  handleUploads = (file) => {
    const fileReader = new FileReader();

    fileReader.onloadend = () => {
      console.log(JSON.parse(fileReader.result))

      try {
        this.setState({
          updatedNewEvent: JSON.parse(fileReader.result),
          file: JSON.parse(fileReader.result),
          fileUpload: false,
        });
      } catch (e) {
        this.setState({
          error: "File is not valid format"
        })
      };
    };

    if (file !== undefined) {
      fileReader.readAsText(file);
    };
  };


  // Toggle Upload Button
  toggleUploadBtn = () => {
    this.state.file ? this.setState({ fileUpload: false }) : this.setState({ fileUpload: true })
  };


  // Has Been Edited
  hasBeenEdited = () => {
    const { updatedEvent, preEvent, updatedNewEvent, preNewEvent } = this.state;
    const validate = updatedEvent !== preEvent || updatedNewEvent !== preNewEvent;


    this.setState({
      hasBeenUpdated: validate ? true : false
    });
  };



  // Update Event Details
  updateEventDetails = (fieldName, e, key) => {
    let value = e.target ? e.target.value : e.value;

    let objValue = key ? this.handleObjValues(fieldName, e, key, this.state.updatedEvent) : false;

    // Some values are not nested, testing against different values
    let u = objValue ?
      objValue
      :
      {
        ...this.state.updatedEvent,
        [fieldName]: value
      };

    this.setState({
      updatedEvent: u
    }, () => this.hasBeenEdited());
  };



  // Create New Event Details
  createEventDetails = (fieldName, e, key) => {
    let value = e.target ? e.target.value : e.value;

    // handle selector values
    if (fieldName == "languages") {
      value = e.map(val => {
        return { value: val.value, label: val.label }
      });
    };

    let objValue = key ? this.handleObjValues(fieldName, e, key, this.state.updatedNewEvent) : false;
    // Some values are not nested, etsting against different values
    let u = objValue ?
      objValue
      :
      {
        ...this.state.updatedNewEvent,
        [fieldName]: value
      };

    this.setState({
      updatedNewEvent: u
    }, () => this.hasBeenEdited(), this.storeState());
  }


  // Handle Object Values
  handleObjValues = (fieldName, e, key, stateVal) => {
    let stateObj;
    let value = e.target ? e.target.value : e.value;
    let stateUpdate = stateVal;

    stateObj = {
      ...stateUpdate[fieldName],
      [key]: value
    };

    stateUpdate[fieldName] = stateObj;
    return stateUpdate
  }


  //Store state for Error Handling Redirects
  storeState = (state) => {
    this.props.history.location.state = state;
  }


  // Redirect User to Form
  redirectUser = () => {
    this.setState({
      newEvent: this.props.history.location.state
    })
  }






  render() {
    const {
      loading,
      error,
      updatedEvent,
      preEvent,
      hasBeenUpdated,
      updatedNewEvent,
      fileUpload,
      file
    } = this.state;

    const { t, event, organisation } = this.props;

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


    // Languages
    const languages = organisation.languages.map(val => {
      return { value: Object.values(val)[0], label: Object.values(val)[1] }
    });


    // format current date for MUI Time Picker
    const currentTime = () => {
      let date = moment().format('h:mm');
      return date.length == 4 ? String(date).padStart(5, '0') : date;
    };

    // Export Event as Json
    const eventJson = encodeURIComponent(
      JSON.stringify(this.state.updatedEvent)
    );


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
      return <div className="card" >
        <div className="alert alert-danger alert-container">
          {error}
        </div>
        <Button onClick={(e) => this.redirectUser()} >Back to Form</Button>
      </div>

    };


    // Create Mode 
    if (!event) {
      return <CreateComponent
        onClickCancel={(e) => this.onClickCancel()}
        languages={languages}
        updatedNewEvent={updatedNewEvent}
        fileUpload={fileUpload}
        t={t}
        fie={file}
        createEvent={(e) => this.createEvent()}
        toggleUploadBtn={(e) => this.toggleUploadBtn()}
        organisation={organisation}
        fileUpload={fileUpload}
        handleUploads={(e) => this.handleUploads(e)}
        createEventDetails={(fieldName, e) => this.createEventDetails(fieldName, e)}
        handleDates={(fieldName, e) => this.handleDates(fieldName, e)}
        hasBeenUpdated={hasBeenUpdated}
      />
    };


    /* Deafault to Edit Mode */
    return (
      <div className="event-config-wrapper">

        <div className="card">

          {/* Export Button */}
          <div className="export-btn-wrapper">
            <Button
              variant="contained"
              href={`data:text/json;charset=utf-8,${eventJson}`}
              download={`event.json`}
            >
              Export
            </Button>
          </div>


          <form>

            {/* Organisation Name */}
            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="organisation_id">
                {t("Organisation")}
              </label>
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
                  {/* For error Redirects whe want to autofill the form where the user left off, thus using updatedEvent not preEvent: see component did mount */}
                  {updatedEvent &&
                    Object.keys(updatedEvent.name).map(val => {
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
                          format={"dd/mm/yyyy"}
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
                          format={"dd/mm/yyyy"}
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
                          format={"dd/mm/yyyy"}
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
                          format={"dd/mm/yyyy"}
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
                          format={"dd/mm/yyyy"}
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
                          format={"dd/mm/yyyy"}
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
                          format={"dd/mm/yyyy"}
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
                          format={"dd/mm/yyyy"}
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
                          format={"dd/mm/yyyy"}
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
                          format={"dd/mm/yyyy"}
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
                          format={"dd/mm/yyyy"}
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
                          format={"dd/mm/yyyy"}
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
            </div>

          </form>

          <hr></hr>

          {/* Form Submittion and Cancel */}
          {hasBeenUpdated &&
            <div className={"form-group row submit event"}>
              <div className={"col-sm-4"}>
                <button
                  className="btn btn-danger btn-lg btn-block"
                  onClick={() => this.onClickCancel()} >
                  {t("Cancel")}
                </button>
              </div>


              <div className={"col-sm-4"}>
                <button
                  onClick={() => this.submitEvent()}
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
