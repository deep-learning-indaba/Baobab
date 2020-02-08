import React, { Component } from "react";
import { eventsService } from "../../../services/events";
import { withRouter } from "react-router";
import FormSelect from "../../../components/form/FormSelect";
import { createColClassName } from "../../../utils/styling/styling";
import DateTimePicker from "react-datetime-picker";

class EventConfigComponent extends Component {
  constructor(props) {
    super(props);
    this.emptyEvent = {
      name: "",
      description: "",
      start_date: Date.now(),
      end_date: Date.now(),
      key: "",
      organisation_id: 1,
      email_from: "",
      url: "",
      application_open: Date.now(),
      application_close: Date.now(),
      review_open: Date.now(),
      review_close: Date.now(),
      selection_open: Date.now(),
      selection_close: Date.now(),
      offer_open: Date.now(),
      offer_close: Date.now(),
      registration_open: Date.now(),
      registration_close: Date.now()
    };
    this.state = {
      preEvent: this.emptyEvent,
      updatedEvent: this.emptyEvent,
      hasBeenUpdated: false,
      loading: true,
      events: [],
      error: "",
      successButtonText: "",
      addingNewEvent: false,
      updatingEvent: false
    };
  }

  componentDidMount() {
    this.getEvents();
  }
  getEvents = () => {
    eventsService.getEvents().then(result => {
      let new_events = result.events.map(event => {
        return { label: event.name, value: event.id, ...event };
      });
      this.setState({
        loading: false,
        events: new_events,
        error: result.error
      });
    });
  };

  updateSelectedEvent = event => {
    eventsService.getEvent(event.id).then(result => {
      this.setState({
        preEvent: result.event,
        updatedEvent: result.event,
        hasBeenUpdated: false,
        successButtonText: "Update Event",
        updatingEvent: true,
        addingNewEvent: false,
        error: result.error
      });
    });
  };

  onClickAddEvent = () => {
    this.setState({
      preEvent: this.emptyEvent,
      updatedEvent: this.emptyEvent,
      hasBeenUpdated: false,
      successButtonText: "Add Event",
      addingNewEvent: true,
      updatingEvent: false
    });
  };

  onClickCancel = () => {
    this.setState({
      preEvent: this.emptyEvent,
      updatedEvent: this.emptyEvent,
      hasBeenUpdated: false,
      successButtonText: "Add Event",
      addingNewEvent: false,
      updatingEvent: false
    });
  };

  onClickSubmit = () => {
    if (this.state.addingNewEvent) {
      // POST
      eventsService.create(this.state.updatedEvent).then(result => {
        this.setState({
          preEvent: result.event,
          updatedEvent: result.event,
          hasBeenUpdated: false,
          successButtonText: "Update Event",
          updatingEvent: true,
          addingNewEvent: false,
          error: result.error
        });
      });
    } else {
      // PUT
      eventsService.update(this.state.updatedEvent).then(result => {
        this.setState({
          preEvent: result.event,
          updatedEvent: result.event,
          hasBeenUpdated: false,
          successButtonText: "Update Event",
          updatingEvent: true,
          addingNewEvent: false,
          error: result.error
        });
      });
    }
    this.getEvents();
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
    let u = { ...this.state.updatedEvent, [fieldName]: e.target.value };

    this.setState({
      updatedEvent: u
    });
    this.hasBeenEdited();
  };

  updateDateTimeEventDetails = (fieldName, value) => {
    let u = { ...this.state.updatedEvent, [fieldName]: value };

    this.setState({
      updatedEvent: u
    });
    this.hasBeenEdited();
  };

  render() {
    const threeColClassName = createColClassName(12, 6, 6, 6);

    const {
      loading,
      events,
      error,
      preEvent,
      updatedEvent,
      hasBeenUpdated,
      successButtonText,
      addingNewEvent,
      updatingEvent
    } = this.state;

    const loadingStyle = {
      width: "3rem",
      height: "3rem"
    };

    if (loading) {
      return (
        <div className="d-flex justify-content-center">
          <div className="spinner-border" style={loadingStyle} role="status">
            <span className="sr-only">Loading...</span>
          </div>
        </div>
      );
    }

    if (error) {
      return <div className="alert alert-danger">{error}</div>;
    }

    return (
      <div>
        <div className="card">
          <div className="row">
            <div className={threeColClassName}>
              <FormSelect
                isDisabled={addingNewEvent}
                options={events}
                id="SelectEvent"
                placeholder="Select event"
                onChange={(id, event) => this.updateSelectedEvent(event)}
                label="Select Event"
                value={{ label: preEvent.name, value: preEvent.id }}
              />
            </div>
            <div className={threeColClassName}>
              <br></br>
              <button
                type="submit"
                className="btn btn-lg btn-primary"
                disabled={updatingEvent}
                onClick={() => this.onClickAddEvent()}
              >
                Add Event
              </button>
            </div>
          </div>
        </div>

        {updatingEvent || addingNewEvent ? (
          <div className="card">
            <form>
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
                  htmlFor="description"
                >
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
                {/* TODO: Replace with Selector, need to get a list of all organisations */}
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor="organisation_id"
                >
                  Organisation
                </label>
                <div className="col-sm-10">
                  <input
                    onChange={e =>
                      this.updateEventDetails("organisation_id", e)
                    }
                    type="text"
                    className="form-control"
                    id="organisation_id"
                    value={updatedEvent.organisation_id}
                  />
                </div>
              </div>
              <div className={"form-group row"}>
                <label className={"col-sm-2 col-form-label"} htmlFor="key">
                  Key
                </label>
                <div className="col-sm-10">
                  <input
                    className={
                      addingNewEvent
                        ? "form-control"
                        : "form-control-plaintext readonly"
                    }
                    onChange={e => {
                      if (addingNewEvent) {
                        this.updateEventDetails("key", e);
                      }
                    }}
                    id="key"
                    value={updatedEvent.key}
                  />
                </div>
              </div>
              <div className={"form-group row"}>
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor="email_from"
                >
                  From email
                </label>
                <div className="col-sm-10">
                  <input
                    onChange={e => this.updateEventDetails("email_from", e)}
                    type="email"
                    className="form-control"
                    id="email_from"
                    value={updatedEvent.email_from}
                  />
                </div>
              </div>
              <div className={"form-group row"}>
                <label className={"col-sm-2 col-form-label"} htmlFor="url">
                  URL
                </label>
                <div className="col-sm-10">
                  <input
                    onChange={e => this.updateEventDetails("url", e)}
                    type="text"
                    className="form-control"
                    id="url"
                    value={updatedEvent.url}
                  />
                </div>
              </div>

              <div className={"form-group row"}>
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor="start_date"
                >
                  Start Date
                </label>
                <div className="col-sm-4">
                  <DateTimePicker
                    clearIcon={null}
                    disableClock={true}
                    onChange={e =>
                      this.updateDateTimeEventDetails("start_date", e)
                    }
                    value={new Date(updatedEvent.start_date)}
                  />
                </div>
                <label className={"col-sm-2 col-form-label"} htmlFor="end_date">
                  End Date
                </label>
                <div className="col-sm-4">
                  <DateTimePicker
                    clearIcon={null}
                    disableClock={true}
                    onChange={e =>
                      this.updateDateTimeEventDetails("end_date", e)
                    }
                    value={new Date(updatedEvent.end_date)}
                  />
                </div>
              </div>
              <div className={"form-group row"}>
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor="application_open"
                >
                  Application Open
                </label>
                <div className="col-sm-4">
                  <DateTimePicker
                    clearIcon={null}
                    disableClock={true}
                    onChange={e =>
                      this.updateDateTimeEventDetails("application_open", e)
                    }
                    value={new Date(updatedEvent.application_open)}
                  />
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
                    value={new Date(updatedEvent.application_close)}
                  />
                </div>
              </div>
              <div className={"form-group row"}>
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor="review_open"
                >
                  Review Open
                </label>
                <div className="col-sm-4">
                  <DateTimePicker
                    clearIcon={null}
                    disableClock={true}
                    onChange={e =>
                      this.updateDateTimeEventDetails("review_open", e)
                    }
                    value={new Date(updatedEvent.review_open)}
                  />
                </div>
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor="review_close"
                >
                  Review Close
                </label>
                <div className="col-sm-4">
                  <DateTimePicker
                    clearIcon={null}
                    disableClock={true}
                    onChange={e =>
                      this.updateDateTimeEventDetails("review_close", e)
                    }
                    value={new Date(updatedEvent.review_close)}
                  />
                </div>
              </div>
              <div className={"form-group row"}>
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor="selection_open"
                >
                  Selection Open
                </label>
                <div className="col-sm-4">
                  <DateTimePicker
                    clearIcon={null}
                    disableClock={true}
                    onChange={e =>
                      this.updateDateTimeEventDetails("selection_open", e)
                    }
                    value={new Date(updatedEvent.selection_open)}
                  />
                </div>
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor="selection_close"
                >
                  Selection Close
                </label>
                <div className="col-sm-4">
                  <DateTimePicker
                    clearIcon={null}
                    disableClock={true}
                    onChange={e =>
                      this.updateDateTimeEventDetails("selection_close", e)
                    }
                    value={new Date(updatedEvent.selection_close)}
                  />
                </div>
              </div>
              <div className={"form-group row"}>
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor="offer_open"
                >
                  Offer Open
                </label>
                <div className="col-sm-4">
                  <DateTimePicker
                    clearIcon={null}
                    disableClock={true}
                    onChange={e =>
                      this.updateDateTimeEventDetails("offer_open", e)
                    }
                    value={new Date(updatedEvent.offer_open)}
                  />
                </div>
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor="offer_close"
                >
                  Offer Close
                </label>
                <div className="col-sm-4">
                  <DateTimePicker
                    clearIcon={null}
                    disableClock={true}
                    onChange={e =>
                      this.updateDateTimeEventDetails("offer_close", e)
                    }
                    value={new Date(updatedEvent.offer_close)}
                  />
                </div>
              </div>
              <div className={"form-group row"}>
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor="registration_open"
                >
                  Registration Open
                </label>
                <div className="col-sm-4">
                  <DateTimePicker
                    clearIcon={null}
                    disableClock={true}
                    onChange={e =>
                      this.updateDateTimeEventDetails("registration_open", e)
                    }
                    value={new Date(updatedEvent.registration_open)}
                  />
                </div>
                <label
                  className={"col-sm-2 col-form-label"}
                  htmlFor="registration_close"
                >
                  Registration Close
                </label>
                <div className="col-sm-4">
                  <DateTimePicker
                    clearIcon={null}
                    disableClock={true}
                    onChange={e =>
                      this.updateDateTimeEventDetails("registration_close", e)
                    }
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
                  onClick={() => this.onClickCancel()}
                >
                  Cancel
                </button>
              </div>
              <div className={"col-sm-4 "}>
                <button
                  onClick={() => this.onClickSubmit()}
                  className="btn btn-success btn-lg btn-block"
                  disabled={!hasBeenUpdated}
                >
                  {successButtonText}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div />
        )}
      </div>
    );
  }
}

export default withRouter(EventConfigComponent);
