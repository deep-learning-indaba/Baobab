import React, { Component } from "react";
import { eventService } from "../../../services/events";
import { Link } from "react-router-dom";
import { withRouter } from "react-router";
import { withTranslation } from 'react-i18next';
import FormTextBox from "../../../components/form/FormTextBox";
import FormTextArea from "../../../components/form/FormTextArea";
import FormDate from "../../../components/form/FormDate";
import FormSelect from "../../../components/form/FormSelect";

//TODO: remove language prompts/description if there is only 1 language in this.props.organisation.languages
class EventConfigComponent extends Component {
  constructor(props) {
    super(props);

    const today_open = this.formatDate(new Date());
    const today_close = this.formatDate(new Date(), "23:59:59");

    this.emptyEvent = {
      name: {},
      description: {},
      start_date: today_open,
      end_date: today_close,
      key: "",
      organisation_id: this.props.organisation.id,
      email_from: this.props.organisation.email_from,
      url: "",
      application_open: today_open,
      application_close: today_close,
      review_open: today_open,
      review_close: today_close,
      selection_open: today_open,
      selection_close: today_close,
      offer_open: today_open,
      offer_close: today_close,
      registration_open: today_open,
      registration_close: today_close,
      event_type: "",
      travel_grant: "",
      miniconf_url: ""
    }

    this.state = {
      updatedEvent: this.emptyEvent,
      isNewEvent: this.props.event && this.props.event.id ? false : true,
      today: today_open,
      allFieldsComplete: false,
      optionalFields: ["miniconf_url"],
      isValid: false,
      loading: false,
      error: "",
      errors: [],
      showErrors: false
    };
  }

  componentDidMount() {
    if (this.props.event) {
      eventService.getEvent(this.props.event.id).then(result => {
        this.setState({
          loading: false,
          updatedEvent: result.event,
          error: result.error
        });
      });
    }
  }

  onClickCreate = () => {
    const isValid = this.validateEventDetails();
    if (isValid) {
      eventService.create(this.state.updatedEvent).then(result => {
        this.setState({
          updatedEvent: result.event,
          error: result.error
        });
        this.props.history.push('/');
      });
    }
    else {
      this.setState({
        showErrors: true
      });
    }
  };

  onClickUpdate = () => {
    const isValid = this.validateEventDetails();
    if (isValid) { //PUT
      eventService.update(this.state.updatedEvent).then(result => {
        this.setState({
        updatedEvent: result.event,
        hasBeenUpdated: false,
        error: result.error
        });
        this.props.history.push('/'); //TODO change this to go to previous page rather than home page, once we've added Edit Event to the Event Details page
      });
    }
    else {
      this.setState({
        showErrors: true
      });
    }
  };

  areAllFieldsComplete = () => {
    //note, since all the dates are set to today's date, they will already be complete
    let allFieldsComplete = true;
    for (var propname in this.state.updatedEvent) {
        if (!this.state.optionalFields.includes(propname) && typeof this.state.updatedEvent[propname] === 'string') {
          if (this.state.updatedEvent[propname].length === 0) {
            allFieldsComplete = false;
          }
        }
        else if (!this.state.optionalFields.includes(propname) && typeof this.state.updatedEvent[propname] === 'object') {
          for (var key in this.state.updatedEvent[propname]) {
            if (this.state.updatedEvent[propname][key].length === 0) {
              allFieldsComplete = false;
            }
          }
        }
      }
    this.setState({
      allFieldsComplete: allFieldsComplete
    });
  };

  getErrorMessages = errors => {
    const errorMessages = [];

    for (let i = 0; i < errors.length; i++) {
      errorMessages.push(
        <div key={"error_"+i} className={"alert alert-danger alert-container"}>
          {errors[i]}
        </div>
      );
    }
    return errorMessages;
  };

  formatDate = (date, set_time_to="00:00:00") => {
    return date.toISOString().split('T')[0]+"T"+set_time_to+"Z";
  }

  validateEventDetails = () => {
    let isValid = true;
    let errors = [];
    this.props.organisation.languages.forEach(lang => {
      if (!this.state.updatedEvent.name || !this.state.updatedEvent.name[lang.code] || this.state.updatedEvent.name[lang.code].length === 0) {
        isValid = false;
        errors.push(this.props.t("Event name in " + lang.description + " is required"));
      }
      if (!this.state.updatedEvent.description || !this.state.updatedEvent.description[lang.code] || this.state.updatedEvent.description[lang.code].length === 0) {
        isValid = false;
        errors.push(this.props.t("Event description in " + lang.description + " is required"));
      }
    });
    if (this.state.updatedEvent.key.length === 0) {
      isValid = false;
      errors.push(this.props.t("Event key is required"));
    }
    if (this.state.updatedEvent.key.length > 16 || this.state.updatedEvent.key.includes(" ")) {
      isValid = false;
      errors.push(this.props.t("Event key must be less than 16 characters and contain no spaces"));
    }
    if (this.state.updatedEvent.event_type.length === 0) {
      isValid = false;
      errors.push(this.props.t("Event type is required"));
    }
    if (this.state.updatedEvent.travel_grant.length === 0) {
      isValid = false;
      errors.push(this.props.t("Award travel grants is required")); 
    }
    if (this.state.updatedEvent.email_from.length === 0) {
      isValid = false;
      errors.push(this.props.t("Organisation email is required"));
    }
    if (!/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(this.state.updatedEvent.email_from)) {
      isValid = false;
      errors.push(this.props.t("Organisation email is invalid"));
    }
    if (this.state.updatedEvent.url.length === 0) {
      isValid = false;
      errors.push(this.props.t("Event URL is required")); //TODO: check if valid URL?
    }
    if (this.state.updatedEvent.application_open < this.state.today) {
      isValid = false;
      errors.push(this.props.t("Application open date cannot be in the past"));
    }
    // working backwards, check each phase ends before the previous phase starts
    if (this.state.updatedEvent.start_date <= this.state.updatedEvent.registration_close) {
      isValid = false;
      errors.push(this.props.t("Event start date must be after registration close date"));
    }
    if (this.state.updatedEvent.registration_open <= this.state.updatedEvent.offer_close) {
      isValid = false;
      errors.push(this.props.t("Registration open date must be after offer close date"));
    }
    if (this.state.updatedEvent.offer_open <= this.state.updatedEvent.selection_close) {
      isValid = false;
      errors.push(this.props.t("Offer open date must be after selection close date"));
    }
    if (this.state.updatedEvent.selection_open <= this.state.updatedEvent.review_close) {
      isValid = false;
      errors.push(this.props.t("Selection open date must be after review close date"));
    }
    if (this.state.updatedEvent.review_open <= this.state.updatedEvent.application_close) {
      isValid = false;
      errors.push(this.props.t("Review open date must be after application close date"));
    }

    //check date ranges
    if (this.state.updatedEvent.application_open > this.state.updatedEvent.application_close) {
      isValid = false;
      errors.push(this.props.t("Application close date must be after application open date"));
    }
    if (this.state.updatedEvent.review_open > this.state.updatedEvent.review_close) {
      isValid = false;
      errors.push(this.props.t("Review close date must be after review open date"));
    }
    if (this.state.updatedEvent.selection_open > this.state.updatedEvent.selection_close) {
      isValid = false;
      errors.push(this.props.t("Selection close date must be after selection open date"));
    }
    if (this.state.updatedEvent.offer_open > this.state.updatedEvent.offer_close) {
      isValid = false;
      errors.push(this.props.t("Offer close date must be after offer open date"));
    }
    if (this.state.updatedEvent.registration_open > this.state.updatedEvent.registration_close) {
      isValid = false;
      errors.push(this.props.t("Registration close date must be after registration open date"));
    }
    if (this.state.updatedEvent.start_date > this.state.updatedEvent.end_date) {
      isValid = false;
      errors.push(this.props.t("Event end date must be after event start date"));
    }
    this.setState({
      errors: errors,
      isValid: isValid
    });
    return isValid;
  };

  updateEventDetails = (fieldName, e, lang) => {
    let u;
    if (lang) {
      u = {
        ...this.state.updatedEvent,
        [fieldName]: {
          ...this.state.updatedEvent[fieldName],
          [lang]: e.target.value
        }
      };
    }
    else {
      u = {
        ...this.state.updatedEvent,
        [fieldName]: e.target.value
      };
    }

    this.setState({
      updatedEvent: u
    },
      () => this.areAllFieldsComplete()
    );
    console.log(this.state.updatedEvent);
  };

  updateDateTimeEventDetails = (fieldName, value, set_time_to) => {
    const u = {
      ...this.state.updatedEvent,
      [fieldName]: this.formatDate(new Date(value), set_time_to)
    };

    this.setState({
      updatedEvent: u
    },
      () => this.areAllFieldsComplete()
    );
    console.log(this.state.updatedEvent);
  };

  updateDropDownEventDetails = (fieldName, dropdown) => {
    const u = {
      ...this.state.updatedEvent,
      [fieldName]: dropdown.value
    };

    this.setState({
      updatedEvent: u
    },
      () => this.areAllFieldsComplete()
    );
    console.log(this.state.updatedEvent);
  };

  render() {
    const {
      loading,
      error,
      errors,
      updatedEvent,
      allFieldsComplete,
      showErrors,
      isNewEvent
    } = this.state;

    const loadingStyle = {
      width: "3rem",
      height: "3rem"
    };

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
    }

    if (error) {
      return <div className="alert alert-danger alert-container">
        {error}
      </div>;
    }

    const t = this.props.t;
    const open_time = "00:00:00";
    const close_time = "23:59:59";

    return (
      <div>
        <div className="card">
          <form>
            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="organisation_name">
                {t("Organisation")}
              </label>

              <div className="col-sm-10">
                <input
                  readOnly
                  type="text"
                  className={"form-control-plaintext readonly"}
                  id="organisation_name"
                  name="organisation_name"
                  value={this.props.organisation.name}
                />
              </div>
            </div>


            {this.props.organisation.languages.map((lang) => (
              <div className={"form-group row"} key={"name_div"+lang.code}>
                <label
                  className={"col-sm-2 col-form-label"} 
                  htmlFor={"name_" + lang.code}>
                  {t("Event Name ("+ lang.description +")")}
                </label>

                <div className="col-sm-10">
                  <FormTextBox
                    id={"name_" + lang.code}
                    name={"name_" + lang.code}
                    type="text"
                    placeholder={t("Name of event in " + lang.description + " (e.g. Deep Learning Indaba 2023)")}
                    required={true}
                    onChange={e => this.updateEventDetails("name", e, lang.code)}
                    value={updatedEvent.name[lang.code]}
                  />
                </div>
              </div>
            ))}

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="event_type">
                {t("Event Type")}
              </label>

              <div className="col-sm-10">
                <FormSelect
                  id="event_type"
                  name="event_type"
                  defaultValue={null || updatedEvent.event_type}
                  required={true}
                  onChange={this.updateDropDownEventDetails}
                  options={[
                    { value: "Event", label: t("Event") },
                    { value: "Award", label: t("Award") },
                    { value: "Call", label: t("Call") },
                    { value: "Programme", label: t("Programme") }
                  ]}
                />
              </div>
            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="travel_grant">
                {t("Awards Travel Grants")}
              </label>

              <div className="col-sm-10">
                <FormSelect
                  id="travel_grant"
                  name="travel_grant"
                  defaultValue={null || updatedEvent.travel_grant}
                  required={true}
                  onChange={this.updateDropDownEventDetails}
                  options={[
                    { value: true, label: t("Yes") },
                    { value: false, label: t("No") }
                  ]}
                />
              </div>
            </div>

            <div className={"form-group row"}>
              <label 
                className={"col-sm-2 col-form-label"}
                htmlFor="key">
                {t("Event Key")}
              </label>

              <div className="col-sm-10">
                <FormTextBox
                  id="key"
                  name="key"
                  type="text"
                  placeholder={t("Event key for URLs (e.g. indaba2023)")}
                  required={true}
                  onChange={e => this.updateEventDetails("key", e)}
                  value={updatedEvent.key}
                />
              </div>
            </div>

            {this.props.organisation.languages.map((lang) => (
              <div className={"form-group row"} key={"description_div"+lang.code}>
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor={"description_" + lang.code}>
                  {t("Event Description ("+ lang.description +")")}
                </label>

                <div className="col-sm-10">
                  <FormTextArea
                    id={"description_" + lang.code}
                    name={"description_" + lang.code}
                    placeholder={t("Description of event in " + lang.description)}
                    required={true}
                    rows={2}
                    onChange={e => this.updateEventDetails("description", e, lang.code)}
                    value={updatedEvent.description[lang.code]}
                  />
                </div>
              </div>
            ))}

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="email_from">
                {t("Email From")}
              </label>

              <div className="col-sm-10">
                <FormTextBox
                  id="email_from"
                  name="email_from"
                  type="email"
                  placeholder={t("Organisation email (e.g. indaba2023@deeplearningindaba.com)")}
                  required={true}
                  value={updatedEvent.email_from}
                  onChange={e => this.updateEventDetails("email_from", e)}
                  />
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"}
                htmlFor="url">
                {t("Event Website")}
              </label>

              <div className="col-sm-10">
                <FormTextBox
                  id="url"
                  name="url"
                  type="text"
                  placeholder={t("Event website (e.g. www.deeplearningindaba.com)")}
                  value={updatedEvent.url}
                  required={true}
                  onChange={e => this.updateEventDetails("url", e)}
                  />
              </div>
            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="application_open">
                {t("Application Open")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="application_open"
                  name="application_open"
                  value={updatedEvent.application_open}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("application_open", e)}/>
              </div>

              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="application_close"
              >
                {t("Application Close")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="application_close"
                  name="application_close"
                  value={updatedEvent.application_close}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("application_close", e, close_time)
                  } />
              </div>

            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="review_open">
                {t("Review Open")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="review_open"
                  name="review_open"
                  value={updatedEvent.review_open}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("review_open", e)} />
              </div>

              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="review_close">
                {t("Review Close")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="review_close"
                  name="review_close"
                  value={updatedEvent.review_close}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("review_close", e, close_time)} />
              </div>
            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="selection_open">
                {t("Selection Open")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="selection_open"
                  name="selection_open"
                  value={updatedEvent.selection_open}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("selection_open", e)} />
              </div>

              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="selection_close">
                {t("Selection Close")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="selection_close"
                  name="selection_close"
                  value={updatedEvent.selection_close}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("selection_close", e, close_time)} />
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="offer_open">
                {t("Offer Open")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="offer_open"
                  name="offer_open"
                  value={updatedEvent.offer_open}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("offer_open", e)} />
              </div>

              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="offer_close">
                {t("Offer Close")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="offer_close"
                  name="offer_close"
                  value={updatedEvent.offer_close}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("offer_close", e, close_time)} />
              </div>
            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="registration_open">
                {t("Registration Open")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="registration_open"
                  name="registration_open"
                  value={updatedEvent.registration_open}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("registration_open", e)} />
              </div>

              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="registration_close">
                {t("Registration Close")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="registration_close"
                  name="registration_close"
                  value={updatedEvent.registration_close}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("registration_close", e, close_time)}/>
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="start_date">
                {t("Event Start Date")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="start_date"
                  name="start_date"
                  value={updatedEvent.start_date}
                  required={true}
                  onChange={e => this.updateDateTimeEventDetails("start_date", e)} />
              </div>

              <label className={"col-sm-2 col-form-label"} htmlFor="end_date">
                {t("Event End Date")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="end_date"
                  name="end_date"
                  value={new Date(updatedEvent.end_date)}
                  required={true}
                  onChange={e => this.updateDateTimeEventDetails("end_date", e, close_time)} />
              </div>
            </div>
          </form>

          <hr></hr>

          <div className={"form-group row"}>
            <div className={"col-sm-4 ml-md-auto"}>
              <Link to=".." className="btn btn-danger btn-lg btn-block">
                {t("Cancel")}
              </Link>
            </div>
            
            <div className={"col-sm-4 "}>
              {isNewEvent ? (
                <button
                  onClick={() => this.onClickCreate()}
                  className="btn btn-success btn-lg btn-block"
                  disabled={!allFieldsComplete}>
                  {t("Create Event")}
                </button>
                ) :
                (
                <button
                  onClick={() => this.onClickUpdate()}
                  className="btn btn-success btn-lg btn-block"
                  disabled={!allFieldsComplete}>
                  {t("Update Event")}
                </button>
              )}
            </div>
          </div>

          <div className={"form-group-row"}>
              {errors && showErrors && this.getErrorMessages(errors)}
            </div>
        </div>
      </div>
    );
  }
}

export default withRouter(withTranslation()(EventConfigComponent));
