
import React, { Component } from 'react'
import ReactTable from 'react-table';
import { NavLink } from 'react-router-dom';
import "react-table/react-table.css";
import { withTranslation } from 'react-i18next';
import './ResponsePage.css'
import { applicationFormService } from '../../services/applicationForm/applicationForm.service'
import { fetchResponse } from '../../services/ResponsePage/ResponsePage'

class ResponsePage extends Component {
    constructor(props) {
        super(props);
        this.state = {
            applicationForm: null,
        }
    };



    componentDidMount() {
        this.fetchForm()
        this.fetchData()
    }



    // Fetch Form
    fetchForm() {
        applicationFormService.getForEvent(this.props.event.id).then(response => {
            this.setState({
                applicationForm: response.formSpec
            })
        })
    }



    // Fetch Data
    fetchData() {
        let params = {
            id: this.props.match.params.id,
            eventKey: this.props.match.params.eventKey,
        }

        fetchResponse(params).then(response => {
            this.setState({
                applicationData: response
            })
        })
    }



    // Go Back
    goBack() {
        this.props.history.goBack();
    }



    // Generate Applciation Status
    applicationStatus() {
        const data = this.state.applicationData;

        if (data) {
            let unsubmitted = !data.is_submitted && !data.is_withdrawn;
            let submitted = data.is_submitted;
            let withdrawn = data.is_withdrawn;

            if (unsubmitted) {
                return ["unsubmitted" + " " + data.started_timestamp]
            }
            if (submitted) {
                return ["submitted" + " " + data.submitted_timestamp]
            }
            if (withdrawn) {
                return ["withdrawn" + " " + data.withdrawn_timestamp]
            }
        }
    }



    // Render Sections
    renderSections() {
        const applicationForm = this.state.applicationForm;
        const applicationData = this.state.applicationData;
        let html = [];
        // Translation
        const t = this.props.t;

        // main function
        if (applicationForm && applicationData) {
            applicationForm.sections.forEach(section => {
                html.push(<div className="section">
                    { /*Heading*/}
                    <div className="flex baseline"><h3>{section.name}</h3><label>{t('Section')}</label></div>
                    { /*Q & A*/}
                    <div className="Q-A">
                        {this.renderQuestions(section)}
                    </div>
                </div>)
            })
        }

        return html
    }



    // Render Questions 
    renderQuestions(section) {
        let questions = section.questions.map(q => {
            return <div className="question-answerer-block">
                <p>{q.headline}</p>
                <h6>{this.renderAnswerer(q.id, q.type)}</h6>
            </div>
        })
        return questions
    }



    // Render Answerers 
    renderAnswerer(id, type) {
        const applicationData = this.state.applicationData;
        const baseUrl = process.env.REACT_APP_API_URL;
        let answers;

        applicationData.answers.forEach(a => {
            if (a.question_id == id) {
                console.log("yes", a.question_id)
                formatAnswerer(a, type)
            }
        })

        // format aswerers 
        function formatAnswerer(a, type) {
            // file
            if (type == "file") {
                answers = <a className="answer file" key={a.value} target="_blank" href={baseUrl + "/api/v1/file?filename=" + a.value}>{a.value}</a>
            }
            // multi-file
            if (type == "multi-file") {
                let files = [];
                a.value.forEach((file => {
                    file ? files.push(
                        <div key={a.headline}><a key={a.headline} target="_blank" href={baseUrl + "/api/v1/file?filename=" + file} className="answer">{a.value}</a></div>
                    )
                        :
                        console.log(`${a.question_id} contains no value`)
                }))
                answers = <div key={a.headline}>{files}</div>
            }
            // choice
            if (type.includes("choice")) {
                let choices = [];
                a.options.forEach(opt => {
                    choices.push(<div key={opt.label}><label className="answer">{opt.label}</label></div>)
                })
                answers = <div key={choices}>{choices}</div>
            }
            // text
            if (type.includes("text")) {
                answers = <div key={a.headline}><p className="answer">{a.value}</p></div>
            }
        }

        return answers
    }


    render() {
        const { applicationForm, applicationData } = this.state
        const applicationStatus = this.applicationStatus();
        const renderSections = this.renderSections();

        // Translation
        const t = this.props.t;
 
        return (
            <div className="table-wrapper">
                {/**/}
                {/*Headings*/}
                <div className="flex baseline"> <h2>{t('Response Page')}</h2> <h4>{this.props.match.params.eventKey}</h4> </div>
                {applicationData &&
                    <div className="headings-lower">
                        <div className="user-details"><label>{t('User Title')}</label> <p>{applicationData.user_title}</p> </div>
                        <div className="user-details"><label>{t('User Id')}</label> <p>{applicationData.user_id}</p> </div>
                        <div className="user-details"><label>{t('First Name')}</label> <p>{applicationData.firstname}</p> </div>
                        <div className="user-details"><label>{t('Last Name')}</label> <p> {applicationData.lastname}</p></div>
                        <div className="user-details"><label>{t('Application Status')}</label> <p>{applicationStatus}</p> </div>
                        <button class="btn btn-primary" onClick={((e) => this.goBack(e))}>Back</button>
                    </div>
                }

                {/*Response Data*/}
                <div className="response-details">
                    {renderSections}
                </div>

            </div>
        )
    }
}

export default withTranslation()(ResponsePage);


