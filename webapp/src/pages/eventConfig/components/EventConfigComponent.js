import React, { Component } from "react";
import { eventService } from "../../../services/events";
import { withRouter } from "react-router";
import DateTimePicker from "react-datetime-picker";
import { withTranslation } from 'react-i18next';
import FormTextBox from "../../../components/form/FormTextBox";
import FormTextArea from "../../../components/form/FormTextArea";
import FormDate from "../../../components/form/FormDate";


class EventConfigComponent extends Component {
  constructor(props) {
    super(props);

    let today = new Date().toLocaleDateString();

    this.emptyEvent = {
      name: "",
      description: "",
      start_date: today,
      end_date: today,
      key: null,
      organisation_id: this.props.organisation.id,
      email_from: "",
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
      hasBeenValidated: false,
      loading: false,
      error: "",
      errors: [],
      showErrors: true
    };
  }

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
    this.setState({
      hasBeenUpdated: isEdited
    });
    this.hasBeenValidated();
  };

  validateEventDetails = () => {
    let isValid = true;
    if (
      !this.state.updatedEvent.name || 
      !this.state.updatedEvent.description || 
      !this.state.updatedEvent.email_from || 
      !this.state.updatedEvent.url) {    
      isValid = false;
    }
    //TODO: potentially add some error reporting
    //this.setState({
    //  errors: errors
    //});
    return isValid;
  };

  validateDateTimeEventDetails = () => {
    let isValid = true;
    let errors = [];
    if (this.state.updatedEvent.application_open <= new Date()) {
      errors.push(this.props.t("Application open date must be in the future"));
    }
    //check date ranges
    if (this.state.updatedEvent.application_open > this.state.updatedEvent.application_close) {
      isValid = false;
      errors.push(this.props.t("Application open date must be before application close date"));
    }
    if (this.state.updatedEvent.review_open > this.state.updatedEvent.review_close) {
      isValid = false;
      errors.push(this.props.t("Review open date must be before review close date"));
    }
    if (this.state.updatedEvent.selection_open > this.state.updatedEvent.selection_close) {
      isValid = false;
      errors.push(this.props.t("Selection open date must be before selection close date"));
    }
    if (this.state.updatedEvent.offer_open > this.state.updatedEvent.offer_close) {
      isValid = false;
      errors.push(this.props.t("Offer open date must be before offer close date"));
    }
    if (this.state.updatedEvent.registration_open > this.state.updatedEvent.registration_close) {
      isValid = false;
      errors.push(this.props.t("Registration open date must be before registration close date"));
    }
    if (this.state.updatedEvent.start_date > this.state.updatedEvent.end_date) {
      isValid = false;
      errors.push(this.props.t("Event start date must be before event end date"));
    }
    // check each phase starts after the next phase ends
    if (this.state.updatedEvent.review_open < this.state.updatedEvent.application_close) {
      isValid = false;
      errors.push(this.props.t("Review open date must be after application close date"));
    }
    if (this.state.updatedEvent.selection_open < this.state.updatedEvent.review_close) {
      isValid = false;
      errors.push(this.props.t("Selection open date must be after review close date"));
    }
    if (this.state.updatedEvent.offer_open < this.state.updatedEvent.selection_close) {
      isValid = false;
      errors.push(this.props.t("Offer open date must be after selection close date"));
    }
    if (this.state.updatedEvent.registration_open < this.state.updatedEvent.offer_close) {
      isValid = false;
      errors.push(this.props.t("Registration open date must be after offer close date"));
    }
    if (this.state.updatedEvent.start_date < this.state.updatedEvent.registration_close) {
      isValid = false;
      errors.push(this.props.t("Event start date must be after registration close date"));
    }

    //this.setState({
    //  errors: errors
    //});
    return isValid;
  };

  hasBeenValidated = () => {
    let isValid = this.validateEventDetails() && this.validateDateTimeEventDetails();
    this.setState({
      hasBeenValidated: isValid
    });
  }

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
      errors,
      updatedEvent,
      hasBeenUpdated,
      hasBeenValidated
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
                htmlFor="organisation_id">
                {t("Organisation")}
              </label>

              <div className="col-sm-10">
                <input
                  readOnly
                  type="text"
                  className={"form-control-plaintext readonly"}
                  id="organisation_id"
                  value={updatedEvent.organisation_id}
                />
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="name">
                {t("Event Name")}
              </label>

              <div className="col-sm-10">
                <FormTextBox
                  id="name"
                  type="text"
                  placeholder="Name of event"
                  required={true}
                  onChange={e => this.updateEventDetails("name", e)}
                  value={updatedEvent.name}
                  showError={!updatedEvent.name}
                  errorText={"Event name is required"}
                />
              </div>
            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="description">
                {t("Description")}
              </label>

              <div className="col-sm-10">
                <FormTextArea
                  id="description"
                  placeholder="Description of event"
                  required={true}
                  rows={2}
                  value={updatedEvent.description}
                  onChange={e => this.updateEventDetails("description", e)}
                  showError={!updatedEvent.description}
                  errorText={"Event description is required"}
                />
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"}
                htmlFor="key">
                {t("Key")}
              </label>

              <div className="col-sm-10">
                <input
                  readOnly
                  className={"form-control-plaintext readonly"}
                  id="key"
                  value={updatedEvent.key} />
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="email_from">
                {t("Email From")}
              </label>

              <div className="col-sm-10">
                <FormTextBox
                  id="email_from"
                  type="email"
                  placeholder="Administrator email"
                  required={true}
                  value={updatedEvent.email_from}
                  onChange={e => this.updateEventDetails("email_from", e)}
                  showError={!updatedEvent.email_from}
                  errorText={"Administrator email is required"} />
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"}
                htmlFor="url">
                {t("URL")}
              </label>
              <div className="col-sm-10">
                <FormTextBox
                  id="url"
                  type="text"
                  placeholder="Event website"
                  value={updatedEvent.url}
                  required={true}
                  onChange={e => this.updateEventDetails("url", e)}
                  showError={!updatedEvent.url}
                  errorText={"Event website is required"} />
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="start_date">
                {t("Start Date")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="start_date"
                  value={new Date(updatedEvent.start_date)}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("start_date", e)} />
              </div>

              <label className={"col-sm-2 col-form-label"} htmlFor="end_date">
                {t("End Date")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="end_date"
                  value={new Date(updatedEvent.end_date)}
                  required={true}
                  onChange={e => this.updateDateTimeEventDetails("end_date", e)} />
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
                  value={new Date(updatedEvent.application_open)}
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
                  value={new Date(updatedEvent.application_close)}
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
                {t("Review Open")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="review_open"
                  value={new Date(updatedEvent.review_open)}
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
                  value={new Date(updatedEvent.review_close)}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("review_close", e)} />
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
                  value={new Date(updatedEvent.selection_open)}
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
                  value={new Date(updatedEvent.selection_close)}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("selection_close", e)} />
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="offer_open">
                {t("Offer Open")}
              </label>

              <div className="col-sm-4">
                <FormDate
                  id="offer_open"
                  value={new Date(updatedEvent.offer_open)}
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
                  value={new Date(updatedEvent.offer_close)}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("offer_close", e)} />
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
                  value={new Date(updatedEvent.registration_open)}
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
                  value={new Date(updatedEvent.registration_close)}
                  required={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("registration_close", e)}/>
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
                disabled={!hasBeenValidated || !hasBeenUpdated}>
                {t("Update Event")}
              </button>
            </div>

          </div>
        </div>
      </div>
    );
  }
}

export default withRouter(withTranslation()(EventConfigComponent));
