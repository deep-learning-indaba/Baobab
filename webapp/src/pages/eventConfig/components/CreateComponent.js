import React, { Component } from "react";
import CloudUploadIcon from '@material-ui/icons/CloudUpload';
import DateTimePicker from "react-datetime-picker";
import Select from 'react-select';
import { withTranslation } from 'react-i18next';
import {
    Button
} from '@material-ui/core';

export class CreateComponent extends Component {
    constructor(props) {
        super(props);

    };



    handleUpdates(fieldName, e) {
        this.props.createEventDetails(fieldName, e)
    }


    handleDates(fieldName, e) {
        this.props.handleDates(fieldName, e)
    }

    onClickSubmit() {
        this.props.createEvent()
    }

    onClickCancel() {
        this.props.onClickCancel()
    }



    render() {

        const {
            t,
            organisation,
            fileUpload,
            newEvent,
            hasBeenUpdated
        } = this.props;


        // Languages
        const languages = organisation.languages.map(val => {
            return { value: Object.values(val)[0], label: Object.values(val)[1] }
        })



        return <div className="create-event-wrapper event-config-wrapper">

            {/* Card Area */}
            <div className="card">

                {/* Import Button */}
                <div className="export-btn-wrapper">

                    <div>

                        <div className="MuiButtonBase-root-wrapper">
                            <Button
                                onClick={(e) => this.toggleUploadBtn(fileUpload)}
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
                            >

                            </input>
                        }
                    </div>
                </div>


                <form>

                    {/* Langauges */}
                    <div className={"form-group row"}>
                        <label
                            className={"col-sm-2 col-form-label"}
                            htmlFor="languages">
                            {t("Langauges")}
                        </label>
                        <div className="col-sm-10">
                            <Select
                                isMulti
                                onChange={e => this.handleUpdates("languages", e)}
                                options={languages}
                            />
                        </div>
                    </div>

                    {/* Conditinal form fields */}
                    {newEvent.languages && newEvent.languages.length == true &&

                        <section>
                            {/* Description */}
                            <div className={"form-group row"}>
                                <label
                                    className={"col-sm-2 col-form-label"}
                                    htmlFor="languages">
                                    {t("Description")}
                                </label>

                                <div className="col-sm-10">
                                    {
                                        newEvent.languages.map(val => {
                                            return <div className="text-area" key={val} >
                                                <textarea
                                                    onChange={e => this.handleUpdates("description", e, val.value)}
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
                                        newEvent.languages.map(val => {
                                            return <div className="text-area" key={val} >
                                                <textarea
                                                    onChange={e => this.handleUpdates("name", e, val.value)}
                                                    className="form-control"
                                                    id="name"
                                                    placeHolder={val.value}
                                                />
                                            </div>
                                        })
                                    }
                                </div>
                            </div>
                        </section>
                    }

                    {/* Key */}
                    <div className={"form-group row"}>
                        <label className={"col-sm-2 col-form-label"}
                            htmlFor="key">
                            {t("Key")}
                        </label>

                        <div className="col-sm-10">
                            <textarea
                                onChange={e => this.handleUpdates("key", e)}
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
                                onChange={e => this.handleUpdates("email_from", e)}
                                type="email"
                                className="form-control"
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
                                onChange={e => this.handleUpdates("url", e)}
                                type="text"
                                className="form-control"
                                id="url"
                            />
                        </div>
                    </div>

                    <hr style={{ "marginTop": "50px" }}></hr>

                    {hasBeenUpdated &&
                        < div className="date-picker-section col-md-12">
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
                                                    format={"dd/mm/yyyy"}
                                                    clearIcon={null}
                                                    disableClock={true}
                                                    onChange={(e) =>
                                                        this.handleDates("start_date", e)}
                                                    value={newEvent.start_date ? new Date(newEvent.start_date) : null} />
                                            </div>
                                        </div>

                                        <div className="date-picker">
                                            <label className={"col-form-label"} htmlFor="end_date">
                                                {t("End Date")}
                                            </label>

                                            <div >
                                                <DateTimePicker
                                                    format={"dd/mm/yyyy"}
                                                    clearIcon={null}
                                                    disableClock={true}
                                                    onChange={e => this.handleDates("end_date", e)}
                                                    value={newEvent.end_date ? new Date(newEvent.end_date) : null} />
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
                                                    format={"dd/mm/yyyy"}
                                                    clearIcon={null}
                                                    disableClock={true}
                                                    onChange={e =>
                                                        this.handleDates("application_open", e)}
                                                    value={newEvent.application_open ? new Date(newEvent.application_open) : null} />
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
                                                    format={"dd/mm/yyyy"}
                                                    clearIcon={null}
                                                    disableClock={true}
                                                    onChange={e =>
                                                        this.handleDates("application_close", e)
                                                    }
                                                    value={newEvent.application_close ? new Date(newEvent.application_close) : null} />
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
                                                    format={"dd/mm/yyyy"}
                                                    clearIcon={null}
                                                    disableClock={true}
                                                    onChange={e =>
                                                        this.handleDates("review_open", e)}
                                                    value={newEvent.review_open ? new Date(newEvent.review_open) : null} />
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
                                                    format={"dd/mm/yyyy"}
                                                    clearIcon={null}
                                                    disableClock={true}
                                                    onChange={e =>
                                                        this.handleDates("review_close", e)}
                                                    value={newEvent.review_close ? new Date(newEvent.review_close) : null} />
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
                                                    format={"dd/mm/yyyy"}
                                                    clearIcon={null}
                                                    disableClock={true}
                                                    onChange={e =>
                                                        this.handleDates("selection_open", e)}
                                                    value={newEvent.selection_open ? new Date(newEvent.selection_open) : null} />
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
                                                    format={"dd/mm/yyyy"}
                                                    clearIcon={null}
                                                    disableClock={true}
                                                    onChange={e =>
                                                        this.handleDates("selection_close", e)}
                                                    value={newEvent.selection_close ? new Date(newEvent.selection_close) : null} />
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
                                                    format={"dd/mm/yyyy"}
                                                    clearIcon={null}
                                                    disableClock={true}
                                                    onChange={e =>
                                                        this.handleDates("offer_open", e)}
                                                    value={newEvent.offer_open ? new Date(newEvent.offer_open) : null} />
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
                                                    format={"dd/mm/yyyy"}
                                                    clearIcon={null}
                                                    disableClock={true}
                                                    onChange={e =>
                                                        this.handleDates("offer_close", e)}
                                                    value={newEvent.offer_close ? new Date(newEvent.offer_close) : null} />
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
                                                    format={"dd/mm/yyyy"}
                                                    clearIcon={null}
                                                    disableClock={true}
                                                    onChange={e =>
                                                        this.handleDates("registration_open", e)}
                                                    value={newEvent.registration_open ? new Date(newEvent.registration_open) : null} />
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
                                                    format={"dd/mm/yyyy"}
                                                    clearIcon={null}
                                                    disableClock={true}
                                                    onChange={e =>
                                                        this.handleDates("registration_close", e)}
                                                    value={newEvent.registration_close ? new Date(newEvent.registration_close) : null}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    }



                </form>
            </div>

            {/* Form Submittion and Cancel */}
            {hasBeenUpdated && newEvent.languages.length == true &&
                <div className={"form-group row submit"}>
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
