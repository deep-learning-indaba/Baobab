
import React, { Component } from 'react'
import "react-table/react-table.css";
import { withTranslation } from 'react-i18next';
import './ResponsePage.css'
import { applicationFormService } from '../../services/applicationForm/applicationForm.service'
import { fetchResponse } from '../../services/responsePage/responsePage.service'

class ResponsePage extends Component {
    constructor(props) {
        super(props);
        this.state = {

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
            id: this.props.match.params.id
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

  
    renderTags() {
        const data = this.state.applicationData;
        if (data) {
            let tags = data.tags.map(tag => {
                return <span class="badge badge-primary">{tag.headline}</span>
            })
            return tags
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
                html.push(<div key={section.name} className="section">
                    { /*Heading*/}
                    <div className="flex baseline"><h3>{section.name}</h3></div>
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
            return <div key={q.id} className="question-answer-block">
                <p>{q.headline}</p>
                <h6>{this.renderAnswer(q.id, q.type)}</h6>
            </div>
        })
        return questions
    }


    // Render Answers 
    renderAnswer(id, type) {
        const applicationData = this.state.applicationData;
        const baseUrl = process.env.REACT_APP_API_URL;
        let answers;

        applicationData.answers.forEach(a => {
            if (a.question_id == id) {
                formatAnswer(a, type)
            }
        })

        // format aswerers 
        function formatAnswer(a, type) {
            // file
            if (type == "file") {
                answers = <a className="answer file" key={a.value} target="_blank" href={baseUrl + "/api/v1/file?filename=" + a.value}>{a.value}</a>
            }
            // multi-file
            if (type == "multi-file") {
                let files = [];
                a.value.forEach((file => {
                    if (file) {
                        files.push(
                            <div key={a.headline}><a key={a.headline} target="_blank" href={baseUrl + "/api/v1/file?filename=" + file} className="answer">{a.value}</a></div>
                        )
                    }
                }))
                answers = <div key={a.headline}>{files}</div>
            }
            // choice
            if (type.includes("choice")) {
                let choices = [];
                a.options.forEach(opt => {
                    if (a.value == opt.value) {
                        choices.push(<div key={opt.label}><label className="answer">{opt.label}</label></div>)
                    }
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
        const tags = this.renderTags()

        // Translation
        const t = this.props.t;

        return (
            <div className="table-wrapper">
                {applicationData &&
                    <div className="headings-lower">
                        <div className="user-details">
                        <h4>{applicationData.user_title} {applicationData.firstname} {applicationData.lastname}</h4>
                        <div className="tags">{tags}</div>
                        </div>

                        <div>
                            <div className="user-details right"><label>{t('Application Status')}</label> <p>{applicationStatus}</p>
                                <button className="btn btn-primary" onClick={((e) => this.goBack(e))}>Back</button>
                            </div>

                        </div>
                    </div>
                }

                {/*Response Data*/}
                {applicationData &&
                    <div className="response-details">
                        {renderSections}
                    </div>
                }

            </div>

        )
    }
}

export default withTranslation()(ResponsePage);


