import React, { Component } from "react";
import DateTimePicker from "react-datetime-picker";
import { eventService } from "../../services/events/events.service";
import Select from 'react-select';
import './newEvent.css';
import { withTranslation } from 'react-i18next';


export class NewEvent extends Component {
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
            organisation_id: this.props.organisation ? this.props.organisation.id : null,
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
    };



    // on Click Cancel
    onClickCancel() {
        this.setState({
            updatedEvent: this.state.preEvent,
            hasBeenUpdated: false
        });
    };



    onClickSubmit() {
        // Create
        eventService.create(this.state.updatedEvent).then(result => {
            console.log(result)
            result.statusCode == 200 ? this.successHandling() : this.errorHandling(Object.values(result.error))
        }).catch(error => {
            this.errorHandling(error)
        });
    };



    // Success Handling
    successHandling() {
        this.setState({
            success: true
        })
        setTimeout(() => {
            this.redirectUser()
        }, 4000)
    }



    // Handle Date Selectors
    handleDates(fieldName, e) {
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
    handleUploads(file) {
        const t = this.props.t;

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
                    error: t("File is not in a valid format")
                })
            };
        };

        if (file !== undefined) {
            fileReader.readAsText(file);
        };
    };



    // Toggle Upload Button
    toggleUploadBtn() {
        this.state.file ? this.setState({ fileUpload: false }) : this.setState({ fileUpload: true })
    };



    // Has Been Edited
    hasBeenEdited() {
        const { updatedEvent, preEvent } = this.state;
        const validate = updatedEvent !== preEvent;


        this.setState({
            hasBeenUpdated: validate ? true : false
        });
    };



    // Create New Event Details
    createEventDetails(fieldName, e, key) {
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
    };



    // Handle Object Values
    handleObjValues(fieldName, e, key, stateVal) {
        let stateObj;
        let value = e.target ? e.target.value : e.value;
        let stateUpdate = stateVal;

        stateObj = {
            ...stateUpdate[fieldName],
            [key]: value
        };

        stateUpdate[fieldName] = stateObj;
        return stateUpdate
    };

    // Redirect User to Form
    redirectUser() {
        this.setState({
            success: true
        }, () => setTimeout(() => {
            this.props.history.push("/")
        }, 4000))
    }

    // Error Handling
    errorHandling(error) {
        const t = this.props.t;

        let errorMessage = error ? error : t("There was an error");
        this.setState({
            error: errorMessage
        }, () => {
            setTimeout(() => {
                window.location.reload()
            }, 3000)
        })
    }


    //Date Values Handler
    dateValHandler(param) {
        if (this.state.updatedEvent) {
            return this.state.updatedEvent[param] ? new Date(this.state.updatedEvent[param]) : null;
        }
    };



    render() {

        const {
            fileUpload,
            updatedEvent,
            hasBeenUpdated,
            file,
            error,
            success
        } = this.state;

        const { t, organisation } = this.props;


        // Languages
        const languages = organisation ? organisation.languages.map(val => {
            return { value: Object.values(val)[0], label: Object.values(val)[1] }
        }) : null ;


        /* Error */
        if (error || !organisation) {
            return <div className="alert alert-danger alert-container">
                {error ? error : t('Network Error')}
            </div>
        };

        /* Success */
        if (success) {
            return <div className="alert alert-success alert-container">
                {t('Success')}
            </div>

        };


        return <div className="create-event-wrapper">

            {/* Card Area */}
            <div className="card">

                {/* Card Heading */}
                <div className="card-heading">
                    <h1>Create</h1>
                    <h5>Event</h5>
                </div>


                {/* Import Button */}
                {!file &&
                    <div className="export-btn-wrapper">
                        <div>
                            <div className="MuiButtonBase-root-wrapper">
                                <button className="btn btn-secondary"
                                    onClick={(e) => this.toggleUploadBtn()}
                                >
                                    {t('Import')}
                                </button>
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

                {/* All Fields */}
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


                    {/* Fields for Uploaded Data */}
                    {file &&
                        <section>
                            {/* Description */}
                            {updatedEvent.description &&
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
                                                            className={"col-sm-2 col-form-label custom-label"}
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
                            }


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
                                                        className={"col-sm-2 col-form-label custom-label"}
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

                        </section>
                    }


                    {/* Fields for User Input */}
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


                    {/* Conditinally Rendered fields - User Input */}
                    {hasBeenUpdated &&
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


                    {/* Divider Line */}
                    <hr style={{ "marginTop": "50px" }}></hr>


                    {/* UTC Time request */}
                    <div className={hasBeenUpdated || file ? "col-md-12 time-warning" : "col-md-12 time-warning disable"}>
                    <span class="badge badge-warning">{t('Times will automatically convert to UTC')}</span>
                    </div>
                    


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
                                                clearIcon={null}
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
                                                clearIcon={null}
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
                                                clearIcon={null}
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
                                                clearIcon={null}
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
                                                clearIcon={null}
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
                                                clearIcon={null}
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
                                                clearIcon={null}
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
                                                clearIcon={null}
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
                                                clearIcon={null}
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
                                                clearIcon={null}
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
                                                clearIcon={null}
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
                                                clearIcon={null}
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
                <div className={"form-group row submit event w-100"}>
                    <div className="col-sm-4">
                        <button
                            className="btn btn-danger btn-lg btn-block"
                            onClick={(e) => this.onClickCancel()} >
                            {t("Cancel")}
                        </button>
                    </div>


                    <div className="col-sm-4">
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

export default withTranslation()(NewEvent);
