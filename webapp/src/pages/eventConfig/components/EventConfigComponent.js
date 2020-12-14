import React, { Component } from "react";
import { eventService } from "../../../services/events/events.service";
import { withRouter } from "react-router";
import DateTimePicker from "react-datetime-picker";
import { withTranslation } from 'react-i18next';
import FormSelect from '../../../components/form/FormSelect';
import { default as ReactSelect } from "react-select";

export class EventConfigComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      preEvent: this.emptyEvent,
      updatedEvent: this.emptyEvent,
      hasBeenUpdated: false,
      loading: true,
      error: "",
      file: null,
      fileUpload: null,
      success: false
    };
  };


  // Populate State
  componentDidMount() {
    // Edit Event
    if (this.props.event) {
      eventService.getEvent(this.props.event.id).then(result => {
        console.log(result)
        this.setState({
          loading: false,
          preEvent: result.event,
          updatedEvent: this.props.history.location.state ? this.props.history.location.state : result.event,
          hasBeenUpdated: false,
          error: result.error
        });
      });
    }
    else {
      // Create Event
      let eventDetails = {
        organisation_id: this.props.organisation ? this.props.organisation.id : null,
        start_date: null,
        end_date: null,
        application_open: null,
        application_close: null,
        review_open: null,
        review_close: null,
        selection_open: null,
        selection_close: null,
        offer_open: null,
        offer_close: null,
        registration_open: null,
        registration_close: null,
      };
      this.setState({
        loading: false,
        preEvent: eventDetails,
        updatedEvent: eventDetails
      });
    }
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
      // Error handling
      result.statusCode == 200 ?
        this.setState({
          preEvent: result.event,
          updatedEvent: result.event,
          hasBeenUpdated: false,
        }, () => this.redirectUser())
        : this.errorHandling(result.error)

    }).catch(result => {
      this.setState({
        error: result.statusCode
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

    this.updateEventDetails(fieldName, dateObj)
  };


  // Has Been Edited
  hasBeenEdited = (objValue) => {
    const { updatedEvent, preEvent } = this.state;
    const validate = updatedEvent !== preEvent;

    console.log(this.state.updatedEvent)

    // Exisitng Object Values that have been updated need to be manually checked 
    this.setState({
      hasBeenUpdated: validate || objValue ? true : false
    });
  };



  // Update Event Details
  updateEventDetails = (fieldName, e, key) => {

    let value = e.target ? e.target.value : e.value;

    let objValue = key ? this.handleObjValues(fieldName, e, key, this.state.updatedEvent) : false;

    // Handle Language
    if (fieldName == "languages") {
      value = e
    }

    // Some values are Objects with values, testing against different values
    let u = objValue ?
      objValue
      :
      {
        ...this.state.updatedEvent,
        [fieldName]: value
      };

    this.setState({
      updatedEvent: u
    }, () => this.hasBeenEdited(objValue));
  };


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


  // Handle Upload
  handleUploads(file) {
    const t = this.props.t;

    const fileReader = new FileReader();

    fileReader.onloadend = () => {
      console.log(JSON.parse(fileReader.result))

      try {
        this.setState({
          updatedEvent: JSON.parse(fileReader.result),
          file: JSON.parse(fileReader.result),
          fileUpload: false,
        }, () => this.hasBeenEdited());
      } catch (e) {
        this.setState({
          error: t("File is not in a valid format")
        })
      };
    };

    if (file !== undefined) {
      fileReader.readAsText(file);
    };
  };



  // Redirect User to Form
  redirectUser = () => {
    this.setState({
      success: true
    }, () => setTimeout(() => {
      this.props.history.push("/")
    }, 4000))
  }

  // Error Handling
  errorHandling(error) {
    let errorMessage = error ? error : "There was an error";
    this.setState({
      error: errorMessage
    }, () => {
      setTimeout(() => {
        window.location.reload()
      }, 3000)
    })
  }

  // Success handling
  successHandling() {
    this.setState({
      success: true
    })
  }

  // toggle Upload Button
  toggleUploadBtn() {
    this.setState({
      fileUpload: true
    })
  }

  //Date Values Handler
  dateValHandler(param) {
    if (this.state.updatedEvent) {
      return this.state.updatedEvent[param] ? new Date(this.state.updatedEvent[param]) : null;
    }
  };

  // Render Date Fields
  renderDateFields() {
    const { hasBeenUpdated, file } = this.state;
    const { t } = this.props;

    return (
      /* Date Form Fields */
      < div className={hasBeenUpdated || file ? "date-picker-section col-md-12" : "date-picker-section col-md-12 disable"}>

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
                    onChange={(e) =>
                      this.handleDates("start_date", e)}
                    value={this.dateValHandler('start_date')} />
                </div>
              </div>

              <div className="date-picker">
                <label className={"col-form-label"} htmlFor="end_date">
                  {t("End Date")}
                </label>

                <div >
                  <DateTimePicker
                    clearIcon={null}
                    onChange={e => this.handleDates("end_date", e)}
                    value={this.dateValHandler('end_date')} />
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
                    onChange={e =>
                      this.handleDates("application_open", e)}
                    value={this.dateValHandler('application_open')} />
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
                    onChange={e =>
                      this.handleDates("application_close", e)
                    }
                    value={this.dateValHandler('application_close')} />
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
                    onChange={e =>
                      this.handleDates("review_open", e)}
                    value={this.dateValHandler('review_open')} />
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
                    onChange={e =>
                      this.handleDates("review_close", e)}
                    value={this.dateValHandler('review_close')} />
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
                    onChange={e =>
                      this.handleDates("selection_open", e)}
                    value={this.dateValHandler('selection_open')} />
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
                    onChange={e =>
                      this.handleDates("selection_close", e)}
                    value={this.dateValHandler('selection_close')} />
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
                    onChange={e =>
                      this.handleDates("offer_open", e)}
                    value={this.dateValHandler('offer_open')} />
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
                    onChange={e =>
                      this.handleDates("offer_close", e)}
                    value={this.dateValHandler('offer_close')} />
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
                    onChange={e =>
                      this.handleDates("registration_open", e)}
                    value={this.dateValHandler('registration_open')} />
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
                    onChange={e =>
                      this.handleDates("registration_close", e)}
                    value={this.dateValHandler('registration_close')}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }


  renderFormSubmit() {
    const { hasBeenUpdated } = this.state;
    const { t } = this.props;

    return (
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
    )
  }



  render() {
    const {
      loading,
      error,
      updatedEvent,
      hasBeenUpdated,
      success,
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
        { value: t("true"), label: t("true") },
        { value: t("false"), label: t("false") },
      ]
    };


    // Export Event as Json
    const eventJson = encodeURIComponent(
      JSON.stringify(this.state.updatedEvent)
    );


    // Languages
    const languages = organisation ? organisation.languages.map(val => {
      return { value: Object.values(val)[0], label: Object.values(val)[1] }
    }) : null;

    const test = [
      { value: "test", label: "test" },
      { value: "123", label: "123" },
    ]


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
      </div>
    };

    /* Success */
    if (success) {
      return <div className="alert alert-success alert-container">
        {t('Success')}
      </div>
    }

    else {
      return (

        <div className="event-config-wrapper">

          <div className="card">

            {/*Create Mode*/}
            {!event &&
              <section>

                {/* Card Heading */}
                <div className="card-heading">
                  <h1>Create</h1>
                  <h5>Event</h5>
                </div>

                {/* Import Button */}
                {!file &&
                  <div className="export-btn-wrapper">
                    <div>
                      <div className="MuiButtonBase-root-wrapper">
                        <button className="btn btn-secondary"
                          onClick={(e) => this.toggleUploadBtn()}
                        >
                          {t('Import')}
                        </button>
                      </div>
                      {fileUpload &&
                        <input
                          type="file"
                          onChange={(e) => this.handleUploads(e.target.files[0])}
                        />
                      }
                    </div>
                  </div>
                }

                {/* All Fields */}
                <form>
                  {/* Langauges */}
                  {!file &&
                    <div className={"form-group row"}>
                      <label
                        className={"col-sm-2 col-form-label"}
                        htmlFor="languages">
                        {t("Langauges")}
                      </label>
                      <div className="col-sm-10">
                        <ReactSelect
                          isMulti
                          options={test}
                          onChange={(e) => this.updateEventDetails("languages", e)}
                        />
                      </div>
                    </div>
                  }


                  {/* Fields for Uploaded Data */}
                  {file &&
                    <section>
                      {/* Description */}
                      {updatedEvent.description &&
                        < div className={"form-group row"}>
                          <label
                            className={"col-sm-2 col-form-label"}
                            htmlFor="languages">
                            {t("Description")}
                          </label>

                          <div className="col-sm-10">
                            {
                              Object.keys(updatedEvent.description).map(val => {
                                return <div>
                                  <div>
                                    <label
                                      className={"col-sm-2 col-form-label custom-label"}
                                      htmlFor="Description">
                                      {val}
                                    </label>
                                  </div>
                                  <div>
                                    < textarea
                                      onChange={e => this.updateEventDetails("name", e)}
                                      className="form-control"
                                      id="name"
                                      value={updatedEvent.description[val]}
                                    />
                                  </div>
                                </div>
                              })
                            }
                          </div>
                        </div>
                      }


                      {/* Name */}
                      <div className={"form-group row"}>
                        <label
                          className={"col-sm-2 col-form-label"}
                          htmlFor="name">
                          {t("Name")}
                        </label>

                        <div className="col-sm-10">
                          {
                            Object.keys(updatedEvent.name).map(val => {
                              return <div>
                                <div>
                                  <label
                                    className={"col-sm-2 col-form-label custom-label"}
                                    htmlFor="name">
                                    {val}
                                  </label>
                                </div>
                                <div>
                                  <textarea
                                    onChange={e => this.updateEventDetails("name", e)}
                                    className="form-control"
                                    id="name"
                                    value={updatedEvent.name[val]}
                                  />
                                </div>
                              </div>
                            })
                          }
                        </div>
                      </div>

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

                    </section>
                  }


                  {/* Fields for User Input */}
                  {hasBeenUpdated && !file &&
                    <div>
                      {/* Description */}
                      < div className={"form-group row"}>
                        <label
                          className={"col-sm-2 col-form-label"}
                          htmlFor="languages">
                          {t("Description")}
                        </label>

                        <div className="col-sm-10">
                          {
                            updatedEvent.languages.map(val => {
                              return <div className="text-area" key={val} >
                                <textarea
                                  onChange={e => this.updateEventDetails("description", e, val.value)}
                                  className="form-control"
                                  id="description"
                                  placeholder={val.value}
                                />
                              </div>
                            })
                          }
                        </div>
                      </div>

                      {/* Name */}
                      <div className={"form-group row"}>
                        <label
                          className={"col-sm-2 col-form-label"}
                          htmlFor="name">
                          {t("Name")}
                        </label>

                        <div className="col-sm-10">
                          {
                            updatedEvent.languages.map(val => {
                              return <div className="text-area" key={val} >
                                <textarea
                                  onChange={e => this.updateEventDetails("name", e, val.value)}
                                  className="form-control"
                                  id="name"
                                  placeHolder={val.value}
                                />
                              </div>
                            })
                          }
                        </div>
                      </div>
                    </div>
                  }


                  {/* Conditinally Rendered fields - User Input */}
                  {hasBeenUpdated &&
                    <section>
                      {/* Key */}
                      <div className={"form-group row"}>
                        <label className={"col-sm-2 col-form-label"}
                          htmlFor="key">
                          {t("Key")}
                        </label>

                        <div className="col-sm-10">
                          <textarea
                            onChange={e => this.updateEventDetails("key", e)}
                            value={updatedEvent.key ? updatedEvent.key : null}
                            className="form-control"
                          />
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
                            value={updatedEvent.email_from ? updatedEvent.email_from : null}
                            id="email_from"
                          />
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
                            value={updatedEvent.url ? updatedEvent.url : null}
                            id="url"
                          />
                        </div>
                      </div>
                    </section>
                  }


                  {/* Divider Line */}
                  <hr style={{ "marginTop": "50px" }}></hr>


                  {/* UTC Time request */}
                  <div className={hasBeenUpdated || file ? "col-md-12 time-warning" : "col-md-12 time-warning disable"}>
                    <span class="badge badge-warning">{t('Enter times in your local time zone, these will automatically be converted to UTC')}</span>
                  </div>

                  {this.renderDateFields()}

                </form>

              </section>
            }

            {/* Edit Mode */}
            {event &&

              <section>
                {/* Export button */}
                <div className="export-btn-wrapper">
                  <button
                    className="btn btn-secondary"
                    variant="contained"
                  >
                    <a href={`data:text/json;charset=utf-8,${eventJson}`}
                      download={`event-${event.key}.json`}>
                      {t('Export')}
                    </a>

                  </button>
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
                        {updatedEvent && updatedEvent.name &&
                          Object.keys(updatedEvent.name).map(val => {
                            return <div key={val} className="col-sm-12 mt-1">
                              <label className={"col-sm-12 custom-label"}>{val}</label>
                              <input
                                onChange={e => this.updateEventDetails("name", e, val)}
                                type="text"
                                className="form-control "
                                id="name"
                                value={updatedEvent.name[val]}
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
                        {updatedEvent && updatedEvent.description ?
                          Object.keys(updatedEvent.description).map(val => {
                            return <div key={val} className="col-sm-12 mt-1">
                              <label className={"col-sm-12 custom-label"}>{val}</label>
                              <textarea
                                onChange={e => this.updateEventDetails("description", e, val)}
                                className="form-control"
                                id="description"
                                value={updatedEvent.description[val]}
                              />
                            </div>
                          })
                          :
                          <div className="col-sm-12 mt-1">
                            <textarea
                              onChange={e => this.updateEventDetails("description", e,)}
                              className="form-control"
                              id="description"
                              value={updatedEvent.description}
                            />
                          </div>
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
                      <FormSelect
                        options={options.eventType}
                        onChange={e => this.updateEventDetails("event_type", e)}
                        value={{ value: `${updatedEvent.event_type}`, label: `${updatedEvent.event_type}` }}
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
                      <option className="custom-label" disabled>{t('Does this event provide travel grants for participants')}</option>
                      <FormSelect
                        onChange={e => this.updateEventDetails("travel_grant", e)}
                        options={options.travelGrant}
                        value={{ value: `${updatedEvent.travel_grant}`, label: `${updatedEvent.travel_grant}` }}
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

                  {/* Review - Number of reviews required */}
                  <div className={"form-group row"}>
                    <label className={"col-sm-2 col-form-label"}
                      htmlFor="url">
                      {t("Reviews Required")}
                    </label>
                    <div className="col-sm-10">
                      <label className="col-sm-12 custom-label">{t('Description: The minimum number of reviews that are required per application response.')}</label>
                      <input
                        onChange={e => this.updateEventDetails("reviewers", e, "num_reviews_required")}
                        type="number"
                        className="form-control"
                        value={updatedEvent.reviewers ? updatedEvent.reviewers.reviews_required : null} />
                    </div>
                  </div>


                  {/* Review - Number of optional reviews */}
                  <div className={"form-group row"}>
                    <label className={"col-sm-2 col-form-label"}
                      htmlFor="url">
                      {t("Number of Optional Reviews")}
                    </label>
                    <div className="col-sm-10">
                      <label className="col-sm-12 custom-label">{t('The number of optional reviews over and above the required number. The total number of reviewers that can be assigned to a response is (Number of reviews required) + (Number of optional reviews)')}</label>
                      <input
                        onChange={e => this.updateEventDetails("reviewers", e, "num_optional_reviews")}
                        type="number"
                        className="form-control"
                        value={updatedEvent.reviewers ? updatedEvent.reviewers.num_optional_reviews : null} />
                    </div>
                  </div>


                  <hr style={{ "marginTop": "50px" }}></hr>

                  {/* UTC Time request */}
                  <div className="col-md-12 time-warning">
                    <span class="badge badge-warning">{t('Enter times in your local time zone, these will automatically be converted to UTC')}</span>
                  </div>

                  {this.renderDateFields()}

                </form>
              </section>

            }
          </div>

          { hasBeenUpdated &&
            this.renderFormSubmit()
          }

        </div>
      )
    }
  }
}

export default withRouter(withTranslation()(EventConfigComponent));





