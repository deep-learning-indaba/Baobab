import React, { Component } from "react";
import { eventService } from "../../../services/events";
import { withRouter } from "react-router";
import DateTimePicker from "react-datetime-picker";

class EventConfigComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      preEvent: this.emptyEvent,
      updatedEvent: this.emptyEvent,
      hasBeenUpdated: false,
      loading: true,
      error: ""
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
      hasBeenUpdated
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

    return (
      <div>
        <div className="card">
          <form>
            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="organisation_id">
                Organisation
              </label>

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

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="name">
                Event Name
              </label>

              <div className="col-sm-10">
                <input
                  onChange={e => this.updateEventDetails("name", e)}
                  type="text"
                  className="form-control"
                  id="name"
                  value={updatedEvent.name}
                />
              </div>
            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="description">
                Description
              </label>

              <div className="col-sm-10">
                <textarea
                  onChange={e => this.updateEventDetails("description", e)}
                  className="form-control"
                  id="description"
                  value={updatedEvent.description}
                />
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"}
                htmlFor="key">
                Key
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
                From email
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
                URL
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

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="start_date">
                Start Date
              </label>

              <div className="col-sm-4">
                <DateTimePicker
                  clearIcon={null}
                  disableClock={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("start_date", e)}
                  value={new Date(updatedEvent.start_date)} />
              </div>

              <label className={"col-sm-2 col-form-label"} htmlFor="end_date">
                End Date
              </label>

              <div className="col-sm-4">
                <DateTimePicker
                  clearIcon={null}
                  disableClock={true}
                  onChange={e => this.updateDateTimeEventDetails("end_date", e)}
                  value={new Date(updatedEvent.end_date)} />
              </div>
            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="application_open">
                Application Open
              </label>

              <div className="col-sm-4">
                <DateTimePicker
                  clearIcon={null}
                  disableClock={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("application_open", e)}
                  value={new Date(updatedEvent.application_open)} />
              </div>

              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="application_close"
              >
                Application Close
              </label>

              <div className="col-sm-4">
                <DateTimePicker
                  clearIcon={null}
                  disableClock={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("application_close", e)
                  }
                  value={new Date(updatedEvent.application_close)} />
              </div>

            </div>
            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="review_open">
                Review Open
              </label>

              <div className="col-sm-4">
                <DateTimePicker
                  clearIcon={null}
                  disableClock={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("review_open", e)}
                  value={new Date(updatedEvent.review_open)} />
              </div>

              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="review_close">
                Review Close
              </label>

              <div className="col-sm-4">
                <DateTimePicker
                  clearIcon={null}
                  disableClock={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("review_close", e)}
                  value={new Date(updatedEvent.review_close)} />
              </div>
            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="selection_open">
                Selection Open
              </label>

              <div className="col-sm-4">
                <DateTimePicker
                  clearIcon={null}
                  disableClock={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("selection_open", e)}
                  value={new Date(updatedEvent.selection_open)} />
              </div>

              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="selection_close">
                Selection Close
              </label>

              <div className="col-sm-4">
                <DateTimePicker
                  clearIcon={null}
                  disableClock={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("selection_close", e)}
                  value={new Date(updatedEvent.selection_close)} />
              </div>
            </div>

            <div className={"form-group row"}>
              <label className={"col-sm-2 col-form-label"} htmlFor="offer_open">
                Offer Open
              </label>

              <div className="col-sm-4">
                <DateTimePicker
                  clearIcon={null}
                  disableClock={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("offer_open", e)}
                  value={new Date(updatedEvent.offer_open)} />
              </div>

              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="offer_close">
                Offer Close
              </label>

              <div className="col-sm-4">
                <DateTimePicker
                  clearIcon={null}
                  disableClock={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("offer_close", e)}
                  value={new Date(updatedEvent.offer_close)} />
              </div>
            </div>

            <div className={"form-group row"}>
              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="registration_open">
                Registration Open
              </label>

              <div className="col-sm-4">
                <DateTimePicker
                  clearIcon={null}
                  disableClock={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("registration_open", e)}
                  value={new Date(updatedEvent.registration_open)} />
              </div>

              <label
                className={"col-sm-2 col-form-label"}
                htmlFor="registration_close">
                Registration Close
              </label>

              <div className="col-sm-4">
                <DateTimePicker
                  clearIcon={null}
                  disableClock={true}
                  onChange={e =>
                    this.updateDateTimeEventDetails("registration_close", e)}
                  value={new Date(updatedEvent.registration_close)}
                />
              </div>
            </div>
          </form>

          <hr></hr>

          <div className={"form-group row"}>
            <div className={"col-sm-4 ml-md-auto"}>
              <button
                className="btn btn-danger btn-lg btn-block"
                onClick={() => this.onClickCancel()} >
                Cancel
              </button>
            </div>

            <div className={"col-sm-4 "}>
              <button
                onClick={() => this.onClickSubmit()}
                className="btn btn-success btn-lg btn-block"
                disabled={!hasBeenUpdated}>
                Update Event
              </button>
            </div>

          </div>
        </div>
      </div>
    );
  }
}

export default withRouter(EventConfigComponent);
