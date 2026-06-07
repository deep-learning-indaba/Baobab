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
      miniconf_url: "",
      contact_email: "",
      image: ""
    }

    this.state = {
      updatedEvent: this.emptyEvent,
      isNewEvent: this.props.event && this.props.event.id ? false : true,
      isMultiLingual: this.props.organisation.languages.length > 1,
      allFieldsComplete: false,
      optionalFields: ["miniconf_url", "contact_email", "image"],
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
    if (u.event_type !== "JOURNAL") {
      for (let i = 0; i < ALL_DATE_FIELDS.length; i++) {
        u[ALL_DATE_FIELDS[i][0]] = u[ALL_DATE_FIELDS[i][0]].substring(0, 10) + "T00:00:00Z"; //start date
        u[ALL_DATE_FIELDS[i][1]] = u[ALL_DATE_FIELDS[i][1]].substring(0, 10) + "T23:59:59Z"; //end date
      }
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
    if (errors.length === 0) { //PUT
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
    if (!/^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/.test(this.state.updatedEvent.email_from)) {
      errors.push(this.props.t("Organisation email is invalid"));
    }
    if (this.state.updatedEvent.url.trim().length === 0) {
      errors.push(this.props.t("Event website is required")); //TODO: check if valid URL?
    }
    
    if (this.state.updatedEvent.event_type !== "JOURNAL") {
      
      if (this.state.isNewEvent && this.state.updatedEvent.application_open < new Date().toISOString().slice(0,10) ) {
        errors.push(this.props.t("Application open date cannot be in the past"));
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4" key={i}>
          <div className="space-y-1">
            <label
              id={open_date_field + "_label"}
              className="block text-sm font-medium text-foreground/80"
              htmlFor={open_date_field}>
              <span className="text-error font-bold mr-1">*</span>
              {this.props.t(open_date_name)}
            </label>
            <FormDate
              id={open_date_field}
              name={open_date_field}
              value={this.state.updatedEvent[open_date_field].slice(0,10)}
              required={true}
              onChange={e => this.updateEventDateTimePicker(open_date_field, e)}
            />
          </div>
          <div className="space-y-1">
            <label
              className="block text-sm font-medium text-foreground/80"
              htmlFor={close_date_field}>
              <span className="text-error font-bold mr-1">*</span>
              {this.props.t(close_date_name)}
            </label>
            <FormDate
              id={close_date_field}
              name={close_date_field}
              value={this.state.updatedEvent[close_date_field].slice(0,10)}
              required={true}
              onChange={e => this.updateEventDateTimePicker(close_date_field, e)}
            />
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

    if (loading) {
      return (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
          {error}
        </div>
      );
    }

    const t = this.props.t;

    return (
      <div className="w-full max-w-5xl mx-auto pt-6 text-left">
        <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-8">
          <h1 className="font-heading text-2xl font-bold text-foreground mb-6">
            {isNewEvent ? t("Create New Event") : t("Event Settings")}
          </h1>
          <form className="space-y-6">
            <div className="space-y-2">
              <label
                className="block text-sm font-semibold text-foreground/90"
                htmlFor="organisation_name">
                {t("Organisation")}
              </label>
              <input
                readOnly
                type="text"
                className="w-full bg-slate-50 border border-border rounded-lg px-4 py-3 text-sm text-muted-foreground outline-none cursor-not-allowed"
                id="organisation_name"
                name="organisation_name"
                value={this.props.organisation.name}
              />
            </div>

            {this.props.organisation.languages.map((lang) => (
              <div className="space-y-2" key={"name_div"+lang.code}>
                <label
                  className="block text-sm font-semibold text-foreground/90" 
                  htmlFor={"name_" + lang.code}>
                  <span className="text-error mr-1">*</span>
                  {isMultiLingual ? t(this.getFieldNameWithLanguage("Event Name", lang.description)) : t("Event Name")}
                </label>
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
            ))}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label
                  className="block text-sm font-semibold text-foreground/90"
                  htmlFor="event_type">
                  <span className="text-error mr-1">*</span>
                  {t("Event Type")}
                </label>
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

              <div className="space-y-2">
                <label
                  className="block text-sm font-semibold text-foreground/90"
                  htmlFor="travel_grant">
                  <span className="text-error mr-1">*</span>
                  {t("Awards Travel Grants")}
                </label>
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

            <div className="space-y-2">
              <label 
                className="block text-sm font-semibold text-foreground/90"
                htmlFor="key">
                <span className="text-error mr-1">*</span>
                {t("Event Key")}
              </label>
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

            {this.props.organisation.languages.map((lang) => (
              <div className="space-y-2" key={"description_div"+lang.code}>
                <label
                  className="block text-sm font-semibold text-foreground/90"
                  htmlFor={"description_" + lang.code}>
                  <span className="text-error mr-1">*</span>
                  {isMultiLingual ? t(this.getFieldNameWithLanguage("Event Description", lang.description)) : t("Event Description")}
                </label>
                <FormTextArea
                  id={"description_" + lang.code}
                  name={"description_" + lang.code}
                  placeholder={isMultiLingual ? t(this.getFieldNameWithLanguage("Description of event", lang.description)) : t("Description of event")}
                  required={true}
                  rows={4}
                  onChange={e => this.updateEventTextField("description", e, lang.code)}
                  value={updatedEvent.description[lang.code]}
                />
              </div>
            ))}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="block text-sm font-semibold text-foreground/90" htmlFor="email_from">
                  <span className="text-error mr-1">*</span>
                  {t("Email From")}
                </label>
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

              <div className="space-y-2">
                <label className="block text-sm font-semibold text-foreground/90" htmlFor="url">
                  <span className="text-error mr-1">*</span>
                  {t("Event Website")}
                </label>
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="block text-sm font-semibold text-foreground/90" htmlFor="contact_email">
                  {t("Support Contact Email")}
                </label>
                <FormTextBox
                  id="contact_email"
                  name="contact_email"
                  type="email"
                  placeholder={t("Contact email shown to applicants (e.g. indabax@example.com)")}
                  value={updatedEvent.contact_email}
                  onChange={e => this.updateEventTextField("contact_email", e)}
                />
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-semibold text-foreground/90" htmlFor="image">
                  {t("Event Image URL")}
                </label>
                <FormTextBox
                  id="image"
                  name="image"
                  type="text"
                  placeholder={t("URL of image to display on event cards")}
                  value={updatedEvent.image}
                  onChange={e => this.updateEventTextField("image", e)}
                />
              </div>
            </div>

            {updatedEvent.event_type && (
              <div className="space-y-6 pt-4 border-t border-border/50">
                <h3 className="text-lg font-semibold text-foreground/90 mb-4">{t("Event Key Dates")}</h3>
                <div className="space-y-6">
                  {this.renderDatePickerTable()}
                </div>
              </div>
            )}
          </form>

          <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-6 border-t border-border/50">
            <Link 
              to=".." 
              className="inline-flex items-center justify-center px-6 py-3 rounded-lg text-sm font-semibold transition-colors bg-error text-error-foreground hover:bg-error/90 shadow-sm w-full md:w-auto text-center"
            >
              {t("Cancel")}
            </Link>
            
            {isNewEvent ? (
              <button
                onClick={() => this.onClickCreate()}
                className="inline-flex items-center justify-center px-6 py-3 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm w-full md:w-auto disabled:opacity-50"
                disabled={!allFieldsComplete}>
                {t("Create Event")}
              </button>
            ) : (
              <button
                onClick={() => this.onClickUpdate()}
                className="inline-flex items-center justify-center px-6 py-3 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm w-full md:w-auto disabled:opacity-50"
                disabled={!allFieldsComplete}>
                {t("Update Event")}
              </button>
            )}
          </div>

          <div className="space-y-2">
            {errors && showErrors && this.getErrorMessages(errors)}
          </div>
        </div>
      </div>
    );
  }
}

export default withRouter(withTranslation()(EventConfigComponent));
