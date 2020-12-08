import React, { Component } from "react";
import { eventService } from "../../../services/events/events.service";
import { withRouter } from "react-router";
import DateTimePicker from "react-datetime-picker";
import { withTranslation } from 'react-i18next';
import FormSelect from '../../../components/form/FormSelect';

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
      success: false
    };
  };


  // Populate State
  componentDidMount() {
    // Redirect if Event prop = false
    if (!this.props.event) {
      this.props.history.push("/newEvent");
    };
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
    // Disable Loading for Create Mode
    else {
      this.setState({
        loading: false
      })
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

    // Exisitng Object Values that have been updated need to be manually checked 
    this.setState({
      hasBeenUpdated: validate || objValue ? true : false
    });
  };



  // Update Event Details
  updateEventDetails = (fieldName, e, key) => {
    let value = e.target ? e.target.value : e.value;

    let objValue = key ? this.handleObjValues(fieldName, e, key, this.state.updatedEvent) : false;

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



  render() {
    const {
      loading,
      error,
      updatedEvent,
      hasBeenUpdated,
      success
    } = this.state;

    const { t, event } = this.props;

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
    };

    /* Navigation Redirects */
    if (!event) {
      return <div className="alert alert-success alert-container">
        {t('This route is not allowed')}
      </div>
    };


    /* Default to Edit Mode */
    if (event) {
      return (
        <div className="event-config-wrapper">

          <div className="card">

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
                    {updatedEvent &&
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
                    {updatedEvent &&
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
                <span class="badge badge-warning">{t('Times will automatically convert to UTC')}</span>
              </div>


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

          </div>

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
      );
    }

  }
}

export default withRouter(withTranslation()(EventConfigComponent));
