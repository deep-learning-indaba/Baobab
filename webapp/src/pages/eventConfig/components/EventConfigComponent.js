import React, { Component } from "react";
import { eventService } from "../../../services/events";
import { Link } from "react-router-dom";
import { withRouter } from "react-router";
import { withTranslation } from 'react-i18next';
import FormTextBox from "../../../components/form/FormTextBox";
import FormTextArea from "../../../components/form/FormTextArea";
import FormDate from "../../../components/form/FormDate";
import FormSelect from "../../../components/form/FormSelect";

const APPLICATION_DATES = ["application_open", "application_close"];
const REVIEW_DATES = ["review_open", "review_close"];
const SELECTION_DATES = ["selection_open", "selection_close"];
const OFFER_DATES = ["offer_open", "offer_close"];
const REGISTRATION_DATES = ["registration_open", "registration_close"];
const EVENT_DATES = ["start_date", "end_date"];
const ALL_DATE_FIELDS = [APPLICATION_DATES, REVIEW_DATES, SELECTION_DATES, OFFER_DATES, REGISTRATION_DATES, EVENT_DATES];
const REQUIRED_DATE_FIELDS_BY_EVENT = {
      "EVENT": ALL_DATE_FIELDS,
      "PROGRAMME": ALL_DATE_FIELDS,
      "AWARD": [APPLICATION_DATES, REVIEW_DATES, SELECTION_DATES, OFFER_DATES],
      "CALL": [APPLICATION_DATES, REVIEW_DATES, SELECTION_DATES],
      "JOURNAL": []
    }
const DATE_NAMES = {
      "application_open": "Application Open",
      "application_close": "Application Close",
      "review_open": "Review Open",
      "review_close": "Review Close",
      "selection_open": "Selection Open",
      "selection_close": "Selection Close",
      "offer_open": "Offer Open",
      "offer_close": "Offer Close",
      "registration_open": "Registration Open",
      "registration_close": "Registration Close",
      "start_date": "Event Start Date",
      "end_date": "Event End Date"
  }

class EventConfigComponent extends Component {
  constructor(props) {
    super(props);

    this.emptyEvent = {
      name: {},
      description: {},
      start_date: "",
      end_date: "",
      key: "",
      organisation_id: this.props.organisation.id,
      email_from: this.props.organisation.email_from,
      url: "",
      application_open: "",
      application_close: "",
      review_open: "",
      review_close: "",
      selection_open: "",
      selection_close: "",
      offer_open: "",
      offer_close: "",
      registration_open: "",
      registration_close: "",
      event_type: "",
      travel_grant: "",
      miniconf_url: ""
    }

    this.state = {
      updatedEvent: this.emptyEvent,
      isNewEvent: this.props.event && this.props.event.id ? false : true,
      isMultiLingual: this.props.organisation.languages.length > 1,
      allFieldsComplete: false,
      optionalFields: ["miniconf_url"],
      requiredDateFields: [],
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
          updatedEvent: this.stripTimeFromDates(result.event), //dates come back from database with times; strip to ensure proper rendering in datetimepickers
          error: result.error,
          requiredDateFields: REQUIRED_DATE_FIELDS_BY_EVENT[result.event.event_type]
        });
      });
    }
  }

  stripTimeFromDates = event => {
    const u = {...event}
    if (u.event_type !== "JOURNAL"){
      for (let i = 0; i < ALL_DATE_FIELDS.length; i++) {
        u[ALL_DATE_FIELDS[i][0]] = u[ALL_DATE_FIELDS[i][0]].substring(0, 10);
        u[ALL_DATE_FIELDS[i][1]] = u[ALL_DATE_FIELDS[i][1]].substring(0, 10);
      }
    }

    return u;
  }

  addTimeToDates = event => {
    const u = {...event}
    for (let i = 0; i < ALL_DATE_FIELDS.length; i++) {
      u[ALL_DATE_FIELDS[i][0]] = u[ALL_DATE_FIELDS[i][0]].substring(0, 10) + "T00:00:00Z"; //start date
      u[ALL_DATE_FIELDS[i][1]] = u[ALL_DATE_FIELDS[i][1]].substring(0, 10) + "T23:59:59Z"; //end date
    }
    return u;
  }

  onClickCreate = () => {
    const errors = this.validateEventDetails();
    if (errors.length === 0) {
      const event_with_times = this.addTimeToDates(this.state.updatedEvent);
      eventService.create(event_with_times).then(result => {
        if (result.error) {
          this.setState({
            errors: [this.props.t(result.error)],
            showErrors: true
          });
        }
        else {
          this.props.history.goBack();
        }});
    }
    else {
      this.setState({
        showErrors: true
      });
    }
  };

  onClickUpdate = () => {
    const errors = this.validateEventDetails();
    if (errors.length == 0) { //PUT
      const event_with_times = this.addTimeToDates(this.state.updatedEvent);
      eventService.update(event_with_times).then(result => {
      if (result.error) {
        this.setState({
          errors: [this.props.t(result.error)],
          showErrors: true
        });
      }
      else {
        this.props.history.goBack();
      }});
    }
    else {
      this.setState({
        showErrors: true
      });
    }
  };

  areAllFieldsComplete = () => {
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
    return allFieldsComplete;
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

  getFieldNameWithLanguage = (input, lang) => {
    return input + " in " + lang;
  }

  validateEventDetails = () => {
    let errors = [];
    this.props.organisation.languages.forEach(lang => {
      if (!this.state.updatedEvent.name || !this.state.updatedEvent.name[lang.code] || this.state.updatedEvent.name[lang.code].trim().length === 0) {
        const error_text = (this.state.isMultiLingual ? this.getFieldNameWithLanguage("Event name", lang.description) : "Event name") + " is required"
        errors.push(this.props.t(error_text));
      }
      if (!this.state.updatedEvent.description || !this.state.updatedEvent.description[lang.code] || this.state.updatedEvent.description[lang.code].trim().length === 0) {
        const error_text = (this.state.isMultiLingual ? this.getFieldNameWithLanguage("Event description", lang.description) : "Event description") + " is required"
        errors.push(this.props.t(error_text));
      }
    });
    if (this.state.updatedEvent.key.trim().length === 0) {
      errors.push(this.props.t("Event key is required"));
    }
    if (this.state.updatedEvent.key.length > 16 || this.state.updatedEvent.key.includes(" ")) {
      errors.push(this.props.t("Event key must be less than 16 characters and contain no spaces"));
    }
    if (this.state.updatedEvent.event_type.length === 0) {
      errors.push(this.props.t("Event type is required"));
    }
    if (this.state.updatedEvent.travel_grant.length === 0) {
      errors.push(this.props.t("Award travel grants is required")); 
    }
    if (this.state.updatedEvent.email_from.trim().length === 0) {
      errors.push(this.props.t("Organisation email is required"));
    }
    if (!/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(this.state.updatedEvent.email_from)) {
      errors.push(this.props.t("Organisation email is invalid"));
    }
    if (this.state.updatedEvent.url.trim().length === 0) {
      errors.push(this.props.t("Event website is required")); //TODO: check if valid URL?
    }
    
    if (this.state.updatedEvent.event_type !== "JOURNAL") {
      
      if (this.state.isNewEvent && this.state.updatedEvent.application_open < new Date().toISOString().slice(0,10) ) {
        errors.push(this.props.t("Application open date cannot be in the past"));
      }

      //working backwards, check each phase ends before the previous phase starts
      if (this.state.requiredDateFields.includes("start_date") && this.state.requiredDateFields.includes("registration_close")) {
        if (this.state.updatedEvent.start_date <= this.state.updatedEvent.registration_close) {
          errors.push(this.props.t("Event start date must be after registration close date"));
        }
      }
      if (this.state.requiredDateFields.includes("registration_open") && this.state.requiredDateFields.includes("review_close")) {
        if (this.state.updatedEvent.registration_open <= this.state.updatedEvent.review_close) {
          errors.push(this.props.t("Registration open date must be after review close date"));
        }
      }
      if (this.state.requiredDateFields.includes("offer_open") && this.state.requiredDateFields.includes("review_close")) {
        if (this.state.updatedEvent.offer_open <= this.state.updatedEvent.review_close) {
          errors.push(this.props.t("Offer open date must be after review close date"));
        }
      }
      if (this.state.updatedEvent.selection_open <= this.state.updatedEvent.review_close) {
        errors.push(this.props.t("Selection open date must be after review close date"));
      }
      //check date ranges
      if (this.state.updatedEvent.application_open >= this.state.updatedEvent.application_close) {
        errors.push(this.props.t("Application close date must be after application open date"));
      }
      if (this.state.updatedEvent.review_open >= this.state.updatedEvent.review_close) {
        errors.push(this.props.t("Review close date must be after review open date"));
      }
      if (this.state.updatedEvent.selection_open >= this.state.updatedEvent.selection_close) {
        errors.push(this.props.t("Selection close date must be after selection open date"));
      }
      if (this.state.requiredDateFields.includes('offer_open') && this.state.requiredDateFields.includes('offer_close')) {
        if (this.state.updatedEvent.offer_open >= this.state.updatedEvent.offer_close) {
          errors.push(this.props.t("Offer close date must be after offer open date"));
        }
      }
      if (this.state.requiredDateFields.includes('registration_open') && this.state.requiredDateFields.includes('registration_close')) {
        if (this.state.updatedEvent.registration_open >= this.state.updatedEvent.registration_close) {
          errors.push(this.props.t("Registration close date must be after registration open date"));
        }
      }
      if (this.state.requiredDateFields.includes('start_date') && this.state.requiredDateFields.includes('end_date')) {
        if (this.state.updatedEvent.start_date >= this.state.updatedEvent.end_date) {
          errors.push(this.props.t("Event end date must be after event start date"));
        }
      }
    }
    return errors;
  };

  updateEventTextField = (fieldName, e, lang) => {
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
    this.updateEventState(u);
  };

  updateEventDateTimePicker = (fieldName, value) => {
    const u = {
      ...this.state.updatedEvent,
      [fieldName]: value
    };
    this.updateEventState(u);
  };

  updateEventDropDown = (fieldName, dropdown) => {
    const u = {
      ...this.state.updatedEvent,
      [fieldName]: dropdown.value
    };
    this.updateEventState(u);
    if (fieldName === "event_type") {
      this.setRequiredDateFields(dropdown.value);
    }
  };

  updateEventState = (event) => {
    this.setState({
      updatedEvent: event
    }, () => {

      const errors = this.validateEventDetails();

      this.setState({
        allFieldsComplete: this.areAllFieldsComplete(),
        errors: errors,
        isValid: errors.length === 0
      });
    });
  }

  setRequiredDateFields = (event_type) => {
    const requiredDateFields = REQUIRED_DATE_FIELDS_BY_EVENT[event_type];

    this.setState({
      requiredDateFields: requiredDateFields,
    }, () => {  
      //checks if event type has been selected. If so, sets all unrequired dates to a future date
      const u = this.state.updatedEvent;
      const future_date = new Date("2099-12-31").toISOString().slice(0,10);
      ALL_DATE_FIELDS.flat().forEach(date => {
        if (!this.state.requiredDateFields.flat().includes(date)) { //if not a required date, set to future_date
          u[date] = future_date;
        }
        else { //if a required date, set to empty string (if it was previously set to future_date), or just keep value as is
          u[date] = u[date] === future_date ? "" : u[date];
        } 
        
      });
      if (this.state.updatedEvent.event_type === "JOURNAL") {
        u.application_open = new Date("2000-12-31").toISOString().slice(0,10);
      }
      this.updateEventState(u);
    }
  );
}

  renderDatePickerTable = () => {
    const datePickers = [];
    
    for (const [i, [open_date_field, close_date_field]] of this.state.requiredDateFields.entries()) {
      const open_date_name = DATE_NAMES[open_date_field];
      const close_date_name = DATE_NAMES[close_date_field];
      datePickers.push(
        <div className={"form-group row"} key={i}>
          <label
            id={open_date_field + "_label"}
            className={"col-sm-2 col-form-label"}
            htmlFor={open_date_field}>
            <span className="required-indicator">*</span>
            {this.props.t(open_date_name)}
          </label>

          <div className="col-sm-4">
            <FormDate
              id={open_date_field}
              name={open_date_field}
              value={this.state.updatedEvent[open_date_field].slice(0,10)}
              required={true}
              onChange={e =>
                this.updateEventDateTimePicker(open_date_field, e)}/>
          </div>

          <label
            className={"col-sm-2 col-form-label"}
            htmlFor={close_date_field}>
            <span className="required-indicator">*</span>
            {this.props.t(close_date_name)}
          </label>

          <div className="col-sm-4">
            <FormDate
              id={close_date_field}
              name={close_date_field}
              value={this.state.updatedEvent[close_date_field].slice(0,10)}
              required={true}
              onChange={e =>
                this.updateEventDateTimePicker(close_date_field, e)} />
          </div>
        </div>
      );
    }
    return datePickers;
  }

  render() {
    const {
      loading,
      error,
      errors,
      updatedEvent,
      allFieldsComplete,
      isMultiLingual,
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
                  <span className="required-indicator">*</span>
                  {isMultiLingual ? t(this.getFieldNameWithLanguage("Event Name", lang.description)) : t("Event Name")}
                </label>

                <div className="col-sm-10">
                  <FormTextBox
                    id={"name_" + lang.code}
                    name={"name_" + lang.code}
                    type="text"
                    placeholder={isMultiLingual ? t(this.getFieldNameWithLanguage("Name of event", lang.description)) : t("Name of event")}
                    required={true}
                    onChange={e => this.updateEventTextField("name", e, lang.code)}
                    value={updatedEvent.name[lang.code]}
                  />
                </div>
              </div>
            ))}

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="event_type">
                <span className="required-indicator">*</span>
                {t("Event Type")}
              </label>

              <div className="col-sm-10">
                <FormSelect
                  id="event_type"
                  name="event_type"
                  defaultValue={updatedEvent.event_type || null}
                  required={true}
                  onChange={this.updateEventDropDown}
                  options={[
                    { value: "EVENT", label: t("Event") },
                    { value: "AWARD", label: t("Award") },
                    { value: "CALL", label: t("Call"),  },
                    { value: "PROGRAMME", label: t("Programme") },
                    { value: "JOURNAL", label: t("Journal") }
                  ]}
                />
              </div>
            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="travel_grant">
                <span className="required-indicator">*</span>
                {t("Awards Travel Grants")}
              </label>

              <div className="col-sm-10">
                <FormSelect
                  id="travel_grant"
                  name="travel_grant"
                  defaultValue={String(updatedEvent.travel_grant) || null}
                  required={true}
                  onChange={this.updateEventDropDown}
                  options={[
                    { value: "true", label: t("Yes") },
                    { value: "false", label: t("No") }
                  ]}
                />
              </div>
            </div>

            <div className={"form-group row"}>
              <label 
                className={"col-sm-2 col-form-label"}
                htmlFor="key">
                <span className="required-indicator">*</span>
                {t("Event Key")}
              </label>

              <div className="col-sm-10">
                <FormTextBox
                  id="key"
                  name="key"
                  type="text"
                  placeholder={t("Event key for URLs (e.g. indaba2023)")}
                  required={true}
                  onChange={e => this.updateEventTextField("key", e)}
                  value={updatedEvent.key}
                />
              </div>
            </div>

            {this.props.organisation.languages.map((lang) => (
              <div className={"form-group row"} key={"description_div"+lang.code}>
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor={"description_" + lang.code}>
                  <span className="required-indicator">*</span>
                  {isMultiLingual ? t(this.getFieldNameWithLanguage("Event Description", lang.description)) : t("Event Description")}
                </label>

                <div className="col-sm-10">
                  <FormTextArea
                    id={"description_" + lang.code}
                    name={"description_" + lang.code}
                    placeholder={isMultiLingual ? t(this.getFieldNameWithLanguage("Description of event", lang.description)) : t("Description of event")}
                    required={true}
                    rows={2}
                    onChange={e => this.updateEventTextField("description", e, lang.code)}
                    value={updatedEvent.description[lang.code]}
                  />
                </div>
              </div>
            ))}

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="email_from">
                <span className="required-indicator">*</span>
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
                  onChange={e => this.updateEventTextField("email_from", e)}
                  />
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"}
                htmlFor="url">
                <span className="required-indicator">*</span>
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
                  onChange={e => this.updateEventTextField("url", e)}
                  />
              </div>
            </div>

            {updatedEvent.event_type && this.renderDatePickerTable()}

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
