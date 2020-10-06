
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
            }, console.log(response.formSpec))
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

        // render answerers
        function renderAnswerer(id, type) {

            // format answerers
            function formatAnswerer(answer, type) {
                const baseUrl = process.env.REACT_APP_API_URL;
                let answers;
                // file
                if (type == "file") {
                    answers = <a key={answer.value} target="_blank" href={baseUrl + "/api/v1/file?filename=" + answer.value}>{answer.value}</a>
                }
                // multi-file
                if (type == "multi-file") {
                    let files = [];
                    answer.value.forEach((file => {
                        file ? files.push(
                            <div key={answer.headline}><a key={answer.headline} target="_blank" href={baseUrl + "/api/v1/file?filename=" + file}>{answer.value}</a></div>
                        )
                            :
                            console.log(`${answer.question_id} contains no value`)
                    }))
                    answers = <div key={answer.headline}>{files}</div>
                }
                // choice
                if (type.includes("choice")) {
                    let choices = [];
                    answer.options.forEach((opt => {
                        choices.push(<div key={opt.label}><label>{opt.label}</label></div>)
                    }))
                    answers = <div key={choices}>{choices}</div>
                }
                // text
                if (answer.type.includes("text")) {
                    answers = <div key={answer.headline} data-tip={answer.value}><p>{answer.value}</p></div>

                }

                let answer;
                applicationData.answers.forEach(a => {
                    if (a.question_id == id) {
                        answer = formatAnswerer(a, type)
                    }
                })

                return answer
            }
        }

            // render questions
            function renderQuestions(section) {
                let questions = section.questions.map(q => {
                    return <div className="question-answerer-block">
                        <p>{q.headline}</p>
                        <h6>{renderAnswerer(q.id, q.type)}</h6>
                    </div>
                })
                return questions
            }

            if (applicationForm && applicationData) {
                applicationForm.sections.forEach(section => {
                    html.push(<div className="section">
                        { /*Heading*/}
                        <div className="flex baseline"><h5>{section.name}</h5><label>Section</label></div>
                        { /*Q & A*/}
                        <div className="Q-A">
                            {renderQuestions(section)}
                        </div>
                    </div>)
                })
            }

            return html
        }


        render() {
            const { applicationForm, applicationData } = this.state
            const applicationStatus = this.applicationStatus();
            const renderSections = this.renderSections();

            return (
                <div className="table-wrapper">
                    {/**/}
                    {/*Headings*/}
                    <div className="flex baseline"> <h2>Response Page </h2> <h4>{this.props.match.params.eventKey}</h4> </div>
                    {applicationData &&
                        <div className="headings-lower">
                            <div className="user-details"><label>User Title</label> <p>{applicationData.user_title}</p> </div>
                            <div className="user-details"><label>User Id</label> <p>{applicationData.user_id}</p> </div>
                            <div className="user-details"><label>First Name</label> <p>{applicationData.firstname}</p> </div>
                            <div className="user-details"><label>Last Name</label> <p> {applicationData.lastname}</p></div>
                            <div className="user-details"><label>applicationStatus</label> <p>{applicationStatus}</p> </div>
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


