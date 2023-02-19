import React, { Component } from "react";
import { eventService } from "../../../services/events";
import { withRouter } from "react-router";
import { withTranslation } from 'react-i18next';
import FormTextBox from "../../../components/form/FormTextBox";
import FormTextArea from "../../../components/form/FormTextArea";
import FormDate from "../../../components/form/FormDate";

class EventConfigComponent extends Component {
  constructor(props) {
    super(props);

    const today = new Date().toLocaleDateString();

    this.emptyEvent = {
      name: "",
      description: "",
      start_date: today,
      end_date: today,
      key: "",
      organisation_id: this.props.organisation.id,
      email_from: this.props.organisation.email_from,
      url: "",
      application_open: today,
      application_close: today,
      review_open: today,
      review_close: today,
      selection_open: today,
      selection_close: today,
      offer_open: today,
      offer_close: today,
      registration_open: today,
      registration_close: today  
    }

    this.state = {
      preEvent: this.emptyEvent,
      updatedEvent: this.emptyEvent,
      hasBeenUpdated: false,
      isValid: false,
      loading: false,
      error: "",
      errors: [],
      showErrors: true
    };
  }

  componentDidMount() {
    if (this.props.event) {
      console.log('here' + this.props.event.id);
      eventService.getEvent(this.props.event.id).then(result => {
        this.setState({
          loading: false,
          preEvent: result.event,
          updatedEvent: result.event,
          hasBeenUpdated: false,
          error: result.error
        });
      });
    }
  }

  onClickCancel = () => {
    this.setState({
      updatedEvent: this.state.preEvent,
      hasBeenUpdated: false
    });
    
  };

  onClickSubmit = () => {
    // PUT
    eventService.update(this.state.updatedEvent).then(result => {
      this.setState({
        preEvent: result.event,
        updatedEvent: result.event,
        hasBeenUpdated: false,
        error: result.error
      });
    });
  };

  hasBeenEdited = () => {
    let isEdited = false;
    for (var propname in this.state.preEvent) {
      if (this.state.updatedEvent[propname] !== this.state.preEvent[propname]) {
        isEdited = true;
      }
    }
    this.validateEventDetails();
    this.setState({
      hasBeenUpdated: isEdited
    });

  };

  getErrorMessages = errors => {
    let errorMessages = [];

    for (let i = 0; i < errors.length; i++) {
      errorMessages.push( //TODO: warning appears for this - each child in list should have key prop
        <div className={"alert alert-danger alert-container"}>
          {errors[i]}
        </div>
      );
    }
    return errorMessages;
  };

  validateEventDetails = () => {
    let isValid = true;
    let errors = [];
    if (this.state.updatedEvent.name.length === 0) {
      isValid = false;
      errors.push(this.props.t("Event name is required"));
    }
    if (this.state.updatedEvent.description.length === 0) {
      isValid = false;
      errors.push(this.props.t("Event description is required"));
    }
    if (this.state.updatedEvent.key.length === 0) {
      isValid = false;
      errors.push(this.props.t("Event key is required"));
    }
    if (this.state.updatedEvent.key.length > 16 || this.state.updatedEvent.key.includes(" ")) {
      isValid = false;
      errors.push(this.props.t("Event key must be less than 16 characters and contain no spaces"));
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
    if (this.state.updatedEvent.application_open < new Date().toLocaleDateString()) {
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
  };

  updateEventDetails = (fieldName, e) => {
    let u = {
      ...this.state.updatedEvent,
      [fieldName]: e.target.value
    };

    this.setState({
      updatedEvent: u
    },
      () => this.hasBeenEdited()
    );
  };

  updateDateTimeEventDetails = (fieldName, value) => {
    let u = {
      ...this.state.updatedEvent,
      [fieldName]: new Date(value).toLocaleDateString()
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
      errors,
      updatedEvent,
      hasBeenUpdated,
      isValid,
      showErrors
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

            <div className={"form-group row"}>
              <label 
                className={"col-sm-2 col-form-label"} 
                htmlFor="name">
                {t("Event Name")+"*"}
              </label>

              <div className="col-sm-10">
                <FormTextBox
                  id="name"
                  name="name"
                  type="text"
                  placeholder={t("Name of event (e.g. Deep Learning Indaba 2023)")}
                  required={true}
                  onChange={e => this.updateEventDetails("name", e)}
                  value={updatedEvent.name}
                />
              </div>
            </div>

            <div className={"form-group row"}>
              <label 
                className={"col-sm-2 col-form-label"}
                htmlFor="key">
                {t("Event Key")+"*"}
              </label>

              <div className="col-sm-10">
                <FormTextBox
                  id="key"
                  name="key"
                  type="text"
                  placeholder={t("Event key (e.g. indaba2023) for URLs")}
                  required={true}
                  onChange={e => this.updateEventDetails("key", e)}
                  value={updatedEvent.key}
                />
              </div>
            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="description">
                {t("Description")+"*"}
              </label>

              <div className="col-sm-10">
                <FormTextArea
                  id="description"
                  name="description"
                  placeholder={t("Description of event")}
                  required={true}
                  rows={2}
                  value={updatedEvent.description}
                  onChange={e => this.updateEventDetails("description", e)}
                />
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="email_from">
                {t("Email From")+"*"}
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
                {t("Event Website")+"*"}
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
                {t("Application Open")+"*"}
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
                {t("Application Close")+"*"}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="application_close"
                  name="application_close"
                  value={updatedEvent.application_close}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("application_close", e)
                  } />
              </div>

            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="review_open">
                {t("Review Open")+"*"}
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
                {t("Review Close")+"*"}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="review_close"
                  name="review_close"
                  value={updatedEvent.review_close}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("review_close", e)} />
              </div>
            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="selection_open">
                {t("Selection Open")+"*"}
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
                {t("Selection Close")+"*"}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="selection_close"
                  name="selection_close"
                  value={updatedEvent.selection_close}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("selection_close", e)} />
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="offer_open">
                {t("Offer Open")+"*"}
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
                {t("Offer Close")+"*"}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="offer_close"
                  name="offer_close"
                  value={updatedEvent.offer_close}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("offer_close", e)} />
              </div>
            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="registration_open">
                {t("Registration Open")+"*"}
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
                {t("Registration Close")+"*"}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="registration_close"
                  name="registration_close"
                  value={updatedEvent.registration_close}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("registration_close", e)}/>
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="start_date">
                {t("Event Start Date")+"*"}
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
                {t("Event End Date")+"*"}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="end_date"
                  name="end_date"
                  value={new Date(updatedEvent.end_date)}
                  required={true}
                  onChange={e => this.updateDateTimeEventDetails("end_date", e)} />
              </div>
            </div>
          </form>

          <hr></hr>

          <div className={"form-group row"}>
            <div className={"col-sm-4 ml-md-auto"}>
              <button
                className="btn btn-danger btn-lg btn-block"
                onClick={() => this.onClickCancel()} >
                {t("Cancel")}
              </button>
            </div>
            
            <div className={"col-sm-4 "}>
              <button
                onClick={() => this.onClickSubmit()}
                className="btn btn-success btn-lg btn-block"
                disabled={!isValid || !hasBeenUpdated}>
                {t("Update Event")}
              </button>
            </div>
          </div>
          {errors && showErrors && this.getErrorMessages(errors)}
        </div>
      </div>
    );
  }
}

export default withRouter(withTranslation()(EventConfigComponent));
