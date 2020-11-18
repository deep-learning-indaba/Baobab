import React, { Component } from "react";
import { eventService } from "../../../services/events";
import { withRouter } from "react-router";
import DateTimePicker from "react-datetime-picker";
import { withTranslation } from 'react-i18next';

class EventConfigComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      preEvent: this.emptyEvent,
      updatedEvent: this.emptyEvent,
      formData: {},
      hasBeenUpdated: false,
      loading: true,
      error: "",
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
          error: Object.values(result.error)
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



  hasBeenEdited = () => {
    const { updatedEvent, preEvent } = this.state;
    const valdiate = updatedEvent !== preEvent;

    this.setState({
      hasBeenUpdated: valdiate ? true : false
    });
  };



  updateEventDetails = (fieldName, key, e) => {
    let u = {
      ...this.state.updatedEvent,
      [fieldName]: {
        [key]: e.target.value
      }
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

    const loadingStyle = {
      width: "3rem",
      height: "3rem"
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
    }

      /* Error */
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

              {/* Organisation Name */}
              <div className="col-sm-10">
                <input
                  readOnly
                  type="text"
                  className={"form-control-plaintext readonly"}
                  id="organisation_id"
                  value={updatedEvent.organisation_name}
                />
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
                      return <div className="col-sm-12 mt-1">
                        <input
                          onChange={e => this.updateEventDetails("name", val, e)}
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
                      return <div className="col-sm-12 mt-1">
                        <textarea
                          onChange={e => this.updateEventDetails("description", val, e)}
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

            {/* Key */}
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
                <input
                  onChange={e => this.updateEventDetails("email_from", e)}
                  type="email"
                  className="form-control"
                  id="email_from"
                  value={updatedEvent.email_from} />
              </div>
            </div>

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


            <hr style={{ "margin-top": "50px" }}></hr>


            {/* Date Picker Section */}
            <div className="date-picker-section col-md-12">
              {/* Left Col */}
              <div className="col-md-4 first-col">

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
                            this.updateDateTimeEventDetails("start_date", e)}
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
                          onChange={e => this.updateDateTimeEventDetails("end_date", e)}
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
                            this.updateDateTimeEventDetails("application_open", e)}
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
                            this.updateDateTimeEventDetails("application_close", e)
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
                            this.updateDateTimeEventDetails("review_open", e)}
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
                            this.updateDateTimeEventDetails("review_close", e)}
                          value={new Date(updatedEvent.review_close)} />
                      </div>
                    </div>

                  </div>
                </div>

              </div>

            
              
              {/* Right Col */}
              <div className="col-md-4 second-col">
             
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
                          this.updateDateTimeEventDetails("selection_open", e)}
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
                          this.updateDateTimeEventDetails("selection_close", e)}
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
                          this.updateDateTimeEventDetails("offer_open", e)}
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
                          this.updateDateTimeEventDetails("offer_close", e)}
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
                          this.updateDateTimeEventDetails("registration_open", e)}
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
                          this.updateDateTimeEventDetails("registration_close", e)}
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
