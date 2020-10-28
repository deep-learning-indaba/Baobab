
import React, { Component } from 'react'
import "react-table/react-table.css";
import { withTranslation } from 'react-i18next';
import './ResponsePage.css'
import { applicationFormService } from '../../services/applicationForm/applicationForm.service'
import { fetchResponse } from '../../services/responsePage/responsePage.service'
import { tagList } from '../../services/tagList/tagList.service'
import { eventService } from '../../services/events/events.service'
import TagModal from './components/TagModal'
import DeleteModal from './components/DeleteModal'
import { tagResponse } from '../../services/responseTag/responseTag.service'

class ResponsePage extends Component {
    constructor(props) {
        super(props);
        this.state = {
            tagMenu: false,
            error: false,
            addNewTags: [],
            eventDetails: {
                event: []
            }
        }
    };

    componentDidMount() {
        this.fetchForm()
        this.fetchData()
        this.fetchTags()
        this.fetchEvent()
    }

    // Tag Functions
    // Fetch Tags
    fetchTags() {
        tagList.list().then(response => {
            this.setState({
                tagList: response
            })
        })
    }


    toggleTags(list) {
        this.setState({
            tagMenu: list ? false : true
        })
    }


    postTag(tag, type) {
        if (type == "responseTag") {
            this.postResponseTag(tag)
        }
        if (type == "tagList") {
            this.postTagList(tag)
        }
    }

    // Post Response API
    postResponseTag(tag) {
        tagResponse.post(tag).then(response => {
            const updateApplicationData = this.state.applicationData
            const updateTagList = this.state.tagList

            if (response.status == 201) {
                let getTag = this.state.tagList.filter(tag => {
                    if (tag.id == response.tag_id) {
                        return tag
                    }
                })

                updateApplicationData.tags.push({ "headline": getTag[0].name, "id": getTag[0].id })
                updateTagList.splice(getTag, 1)
                this.setState({
                    applicationData: updateApplicationData,
                    error: false
                })
            }
        }).catch((error) => {
            console.log(error)
            this.setState({
                error: error.message
            })
        })
    }

    // Post Tag List API
    postTagList(tags) {
        let updateApplicationData = this.state.applicationData
        let updateEventDetails = this.state.eventDetails
        let newTags = Object.values(tags)

        tagList.post(tags).then(response => {
            if (response.status == 201) {
                tagResponse.post(tags).then(response => {
                    if (response.status == 201) {
                        newTags.forEach(val => {
                            if (updateEventDetails.event.includes(val.id)) {
                                updateEventDetails.event.splice([val.id], 1)
                            }
                            updateApplicationData.tags.push(val)
                        });
                        this.setState({
                            applicationData: updateApplicationData,
                            eventDetails: updateEventDetails
                        })
                    }
                })
            }
        })

    }

    /*
     saveNewTag() {
            const updateApplicationData = this.state.applicationData
            tagList.post().then(response => {
                if (response.status == 200) {
                    tagResponse.post().then(response => {
                        updateApplicationData.tags.push(response.tag)
                        this.setState({
                            applicationData: updateApplicationData
                        })
                    })
                }
            }).catch((error) => {
                this.setState({
                    error: true
                })
            })
        }
    */


    deleteTag(tag_id) {
        let updateApplicationData = this.state.applicationData
        let error;
        tagList.remove({
            "tag_id": tag_id,
            "response_id": parseInt(this.props.match.params.id),
            "event_id": this.props.event.id
        }).then(response => {
            if (response.status == 201) {
                updateApplicationData.tags.forEach((tag, index) => {
                    if (tag.id == tag_id) {
                        updateApplicationData.tags.splice(index, 1)
                    }
                })
            }
        }).catch((error) => {
            error = error.message
        })

        this.setState({
            applicationData: updateApplicationData,
            deleteModal: null,
            error: error
        })
    }



    // Data Functions
    // Fetch Event Details
    fetchEvent() {
        eventService.getEvent().then(response => {
            console.log(response)
            this.setState({
                eventDetails: {
                    event: ["en", "fr"]
                }
            })
        })
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



    // Render Page HTML
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
                    if (a.value == opt.valuel) {
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


    renderTags() {
        const data = this.state.applicationData;
        if (data) {
            let tags = data.tags.map(tag => {
                return <span
                    onClick={(e) => this.deleteTag(tag.id)}
                    className="btn badge badge-info"
                    data-toggle="modal"
                    data-target="#exampleModal2"
                >
                    {tag.headline}
                    <i className="far fa-trash-alt"></i></span>
            })
            return tags
        }
    }


    renderTagModal() {
        const { eventDetails } = this.state;
        if (eventDetails) {
            return <TagModal
                postTag={(tags) => this.postTag(tags, "tagList")}
                eventDetails={eventDetails}
            />
        }
    }


    renderDeleteModal() {
        const { eventDetails } = this.state;
        if (eventDetails) {
            return <DeleteModal
                handleSubmit={(tag_id) => this.deleteTag(tag_id)}
                deleteQue={this.state.deleteModal}
            />
        }
    }

    setDeleteModal(tag_id) {
        this.setState({
            deleteModal: tag_id
        })
    }


    render() {
        const { applicationData, tagList, tagMenu, error } = this.state
        const applicationStatus = this.applicationStatus();
        const renderSections = this.renderSections();
        const tags = this.renderTags()
        const tagModal = this.renderTagModal()
        const deleteModal = this.renderDeleteModal()

        // Translation
        const t = this.props.t;

        return (
            <div className="table-wrapper">

                {/* API Error */}
                {error &&
                    <div className="alert alert-danger" role="alert">
                        <p>{error}</p>
                    </div>
                }

                {/* Add Tag Modal*/}
                {tagModal}
                {deleteModal}


                {/* Headings */}
                {applicationData &&
                    <div className="headings-lower">
                        <div className="user-details">
                            <h2>{applicationData.user_title} {applicationData.firstname} {applicationData.lastname}</h2>
                            <div className="tags">
                                {tags}
                            <span onClick={(e) => this.toggleTags(tagMenu)} className={tagMenu && tagList.length ?"badge add-tags active" : "badge add-tags"}>Add tag</span>
                            </div>

                            {/*Tag List*/}
                            <div className={tagMenu && tagList.length ? "tag-response show" : "tag-response"}>
                                {tagList &&
                                    tagList.map(val => {
                                        return <div className="tag-item" key={val.id} >
                                            <button
                                                onClick={(e) => this.postTag(
                                                    {
                                                        "tag_id": val.id,
                                                        "response_id": parseInt(this.props.match.params.id),
                                                        "event_id": this.props.event.id
                                                    }, "responseTag"
                                                )} class="btn tag">{val.name}</button>
                                        </div>
                                    })}


                                {this.state.eventDetails.event.length > 0 &&
                                    <button data-toggle="modal" type="button" className="btn btn-primary" data-target="#exampleModal">
                                        New tag
                                     </button>
                                }

                            </div>

                        </div>

                        {/* User details Right Tab */}
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


