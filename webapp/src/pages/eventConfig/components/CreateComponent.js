import React, { Component } from "react";
import CloudUploadIcon from '@material-ui/icons/CloudUpload';
import DateTimePicker from "react-datetime-picker";
import { eventService } from "../../../services/events/events.service";
import Select from 'react-select';
import { withTranslation } from 'react-i18next';
import {
    Button,
    TextField
} from '@material-ui/core';

export class CreateComponent extends Component {
    constructor(props) {
        super(props);

        this.state = {
            preEvent: this.emptyEvent,
            updatedEvent: this.emptyEvent,
            loading: true,
            error: "",
            fileUpload: null,
            file: null,
            success: false
        };
    };

    componentDidMount() {
        // Create Event
        let eventDetails = {
            organisation_id: this.props.organisation.id,
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


    // on Click Cancel
    onClickCancel = () => {
        this.setState({
            updatedEvent: this.state.preEvent,
            hasBeenUpdated: false
        });
    };


    createEvent = () => {
        // Create
        eventService.create(this.state.updatedEvent).then(result => {
            console.log(result)
            this.setState({
                preEvent: result.event,
                updatedEvent: result.event,
                hasBeenUpdated: false,
                error: Object.values(result.error)
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

        this.createEventDetails(fieldName, dateObj)
    };


    // Handle Upload
    handleUploads = (file) => {
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
                    error: "File is not valid format"
                })
            };
        };

        if (file !== undefined) {
            fileReader.readAsText(file);
        };
    };


    // Toggle Upload Button
    toggleUploadBtn = () => {
        this.state.file ? this.setState({ fileUpload: false }) : this.setState({ fileUpload: true })
    };


    // Has Been Edited
    hasBeenEdited = () => {
        const { updatedEvent, preEvent } = this.state;
        const validate = updatedEvent !== preEvent;


        this.setState({
            hasBeenUpdated: validate ? true : false
        });
    };


    // Create New Event Details
    createEventDetails = (fieldName, e, key) => {
        let value = e.target ? e.target.value : e.value;

        // handle selector values
        if (fieldName == "languages") {
            value = e.map(val => {
                return { value: val.value, label: val.label }
            });
        };

        let objValue = key ? this.handleObjValues(fieldName, e, key, this.state.updatedEvent) : false;
        // Some values are not nested, etsting against different values
        let u = objValue ?
            objValue
            :
            {
                ...this.state.updatedEvent,
                [fieldName]: value
            };

        this.setState({
            updatedEvent: u
        }, () => this.hasBeenEdited());
    }


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


    //Date Values Handler
    dateValHandler(param) {
        return this.state.hasBeenUpdated || this.state.file ? new Date(this.state.updatedEvent[param]) : null;
    }





    render() {

        const {
            fileUpload,
            updatedEvent,
            hasBeenUpdated,
            file,
            preEvent
        } = this.state;

        const { t, organisation } = this.props;




        // Languages
        const languages = organisation.languages.map(val => {
            return { value: Object.values(val)[0], label: Object.values(val)[1] }
        });


        return <div className="create-event-wrapper event-config-wrapper">

            {/* Card Area */}
            <div className="card">

                {/* Import Button */}
                {!file &&
                    <div className="export-btn-wrapper">
                        <div>
                            <div className="MuiButtonBase-root-wrapper">
                                <Button
                                    onClick={(e) => this.toggleUploadBtn()}
                                    variant="contained"
                                    color="default"
                                    startIcon={<CloudUploadIcon />}
                                >
                                    Import
                  </Button>
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
                                <Select
                                    isMulti
                                    onChange={e => this.createEventDetails("languages", e)}
                                    options={languages}
                                />
                            </div>
                        </div>
                    }

            
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
                                                    onChange={e => this.createEventDetails("description", e, val.value)}
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
                                                    onChange={e => this.createEventDetails("name", e, val.value)}
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



                    {file &&
                        <section>
                            {/* Description */}
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
                                                        className={"col-sm-2 col-form-label"}
                                                        htmlFor="Description">
                                                        {val}
                                                    </label>
                                                </div>
                                                <div>
                                                    < textarea
                                                        onChange={e => this.createEventDetails("name", e)}
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
                                                        className={"col-sm-2 col-form-label"}
                                                        htmlFor="name">
                                                        {val}
                                                    </label>
                                                </div>
                                                <div>
                                                    < textarea
                                                        onChange={e => this.createEventDetails("name", e)}
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
                        

                            {/* Event Type */}
                            {updatedEvent.event_type &&
                                <div className={"form-group row"}>
                                    <label className={"col-sm-2 col-form-label"}
                                        htmlFor="event-type">
                                        {t("Event Type")}
                                    </label>

                                    <div className="col-sm-10">
                                        <Select
                                            onChange={e => this.createEventDetails("event_type", e)}
                                            value={updatedEvent.event_type}
                                        />
                                    </div>
                                </div>
                            }


                            {/* Travel Grants */}
                            {updatedEvent.travel_grant &&

                                < div className={"form-group row"}>
                                    <label className={"col-sm-2 col-form-label"}
                                        htmlFor="travel-grants">
                                        {t("Travel Grants")}
                                    </label>

                                    <div className="col-sm-10">
                                        <option disabled>{t('Does this event provide travel grants for participants')}</option>
                                        <Select
                                            onChange={e => this.createEventDetails("travel_grant", e)}
                                            value={updatedEvent.travel_grant}
                                        />
                                    </div>
                                </div>
                            }


                            {/* Miniconf Url */}
                            {updatedEvent.miniconf_url &&
                                <div className={"form-group row"}>
                                    <label className={"col-sm-2 col-form-label"}
                                        htmlFor="travel-grants">
                                        {t("MiniConf Url")}
                                    </label>

                                    <div className="col-sm-10">
                                        <textarea
                                            value={updatedEvent.miniconf_url}
                                            className="w-100"
                                            placeholder={t("If this is a virtual MiniConf event, enter the URL to the miniconf site")}
                                            onChange={e => this.createEventDetails("miniconf_url", e)}
                                            className="form-control"
                                            id="description"
                                        />
                                    </div>
                                </div>
                            }


                            {/* Time */}
                            {updatedEvent.time &&
                                <div className={"form-group row"}>
                                    <label className={"col-sm-2 col-form-label"}
                                        htmlFor="url">
                                        {t("Time")}
                                    </label>
                                    <div className="col-sm-10">
                                        <TextField
                                            onChange={e => this.createEventDetails("time", e)}
                                            id="time"
                                            label="Times are in UTC"
                                            type="time"
                                            value={updatedEvent.time}
                                            InputLabelProps={{
                                                shrink: true,
                                            }}
                                            inputProps={{
                                                step: 300, // 5 min
                                            }}
                                        />
                                    </div>
                                </div>
                            }
                        </section>

                    }


                    {/* Conditinal form fields */}
                    {hasBeenUpdated || file &&
                        <section>
                            {/* Key */}
                            <div className={"form-group row"}>
                                <label className={"col-sm-2 col-form-label"}
                                    htmlFor="key">
                                    {t("Key")}
                                </label>

                                <div className="col-sm-10">
                                    <textarea
                                        onChange={e => this.createEventDetails("key", e)}
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
                                        onChange={e => this.createEventDetails("email_from", e)}
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
                                        onChange={e => this.createEventDetails("url", e)}
                                        type="text"
                                        className="form-control"
                                        value={updatedEvent.url ? updatedEvent.url : null}
                                        id="url"
                                    />
                                </div>
                            </div>
                        </section>
                    }


                    <hr style={{ "marginTop": "50px" }}></hr>


                    {/* Date Form Fields */}
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
                                                format={"MM/dd/yyyy"}
                                                clearIcon={null}
                                                disableClock={true}
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
                                                format={"MM/dd/yyyy"}
                                                clearIcon={null}
                                                disableClock={true}
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
                                                format={"MM/dd/yyyy"}
                                                clearIcon={null}
                                                disableClock={true}
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
                                                format={"MM/dd/yyyy"}
                                                clearIcon={null}
                                                disableClock={true}
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
                                                format={"MM/dd/yyyy"}
                                                clearIcon={null}
                                                disableClock={true}
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
                                                format={"MM/dd/yyyy"}
                                                clearIcon={null}
                                                disableClock={true}
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
                                                format={"MM/dd/yyyy"}
                                                clearIcon={null}
                                                disableClock={true}
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
                                                format={"MM/dd/yyyy"}
                                                clearIcon={null}
                                                disableClock={true}
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
                                                format={"MM/dd/yyyy"}
                                                clearIcon={null}
                                                disableClock={true}
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
                                                format={"MM/dd/yyyy"}
                                                clearIcon={null}
                                                disableClock={true}
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
                                                format={"MM/dd/yyyy"}
                                                clearIcon={null}
                                                disableClock={true}
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
                                                format={"MM/dd/yyyy"}
                                                clearIcon={null}
                                                disableClock={true}
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


                </form>
            </div>

            
            {/* Form Submittion and Cancel */}
            {
                hasBeenUpdated &&
                <div className={"form-group row submit event"}>
                    <div className={"col-sm-4"}>
                        <button
                            className="btn btn-danger btn-lg btn-block"
                            onClick={(e) => this.onClickCancel()} >
                            {t("Cancel")}
                        </button>
                    </div>


                    <div className={"col-sm-4"}>
                        <button
                            onClick={(e) => this.onClickSubmit()}
                            className="btn btn-success btn-lg btn-block"
                            disabled={!hasBeenUpdated}
                        >
                            {t("Update Event")}
                        </button>
                    </div>
                </div>
            }
        </div >
    };
}

export default withTranslation()(CreateComponent);
