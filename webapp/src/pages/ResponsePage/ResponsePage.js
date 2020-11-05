
import React, { Component } from 'react'
import "react-table/react-table.css";
import './ResponsePage.css'
import { withTranslation } from 'react-i18next';
import TagModal from './components/TagModal'
import DeleteModal from './components/DeleteModal'
import { eventService } from '../../services/events/events.service'
import { tagResponse } from '../../services/responseTag/responseTag.service'
import { applicationFormService } from '../../services/applicationForm/applicationForm.service'
import { fetchResponse } from '../../services/responsePage/responsePage.service'
import { tagList } from '../../services/responseTag/tags.service'


class ResponsePage extends Component {
    constructor(props) {
        super(props);
        this.state = {
            tagMenu: false,
            error: false,
            addNewTags: [],
            eventLanguages: []
        }
    };

    componentDidMount() {
        this.fetchForm();
        this.fetchData();
        this.fetchTags();
        this.fetchEvent();
    }

    // Data Functions
    // Fetch Event Details
    fetchEvent() {
        eventService.getEvent().then(response => {
            this.setState({
                eventLanguages: ["en", "fr"]
            })
        });
    }


    // Fetch Form
    fetchForm() {
        applicationFormService.getForEvent(this.props.event.id).then(response => {
            this.setState({
                applicationForm: response.formSpec
            })
        });
    }


    // Fetch Data
    fetchData() {
        let params = {
            id: this.props.match.params.id
        };
        fetchResponse(params).then(response => {
            this.setState({
                applicationData: response
            })
        });
    }


    // Misc FUnctions
    // Go Back
    goBack() {
        this.props.history.goBack();
    }


    error(error) {
        this.setState({
            error: error
        })
    }


    // Tag Functions
    // Populate tag list
    fetchTags() {
        tagList.list().then(response => {
            this.setState({
                tagList: response
            })
        });
    }


    // Toggle Tag Menu
    toggleTags(list) {
        this.setState({
            tagMenu: list ? false : true
        })
    }


    // Post Tag
    postTag(tag, type) {
        if (type == "responseTag") {
            this.postResponseTag(tag)
        }
        else {
            this.postTagList(tag)
        }
    }



    // Post Response API
    postResponseTag(tag) {
        const updateApplicationData = this.state.applicationData;
        const updateTagList = this.state.tagList;

        tagResponse.post(tag).then(response => {
            if (response.status == 201) {
                const getTag = this.state.tagList.find(tag => tag.id === response.tag_id);
                updateApplicationData.tags.push({ "headline": getTag.name, "id": getTag.id });
                updateTagList.splice(getTag, 1);

                this.setState({
                    applicationData: updateApplicationData,
                });
            };
        }).catch((response) => {
            this.error(response.message)
        });
    }



    // Post Tag List API
    postTagList(tags) {
        let updateApplicationData = this.state.applicationData;
        let updateEventLanguages = this.state.eventLanguages;
        const newTags = Object.values(tags);
        let filterTags = tags;

        // filter dulicate headlines (bug fix)  
        updateApplicationData.tags.forEach((tag1) => {
            newTags.forEach((tag2) => {
                if (tag1.headline == tag2.headline) {
                    delete filterTags[tag2.id]
                };
            })
        });

        if (Object.keys(filterTags).length) {
            tagList.post(filterTags).then(response => {
                if (response.status == 201) {
                    tagResponse.post(filterTags).then(response => {
                        if (response.status == 201) {
                            // add tags to state
                            newTags.forEach(val => {
                                if (val.id == this.props.i18n.language) {
                                    updateApplicationData.tags.push(val)
                                }
                            })


                            this.setState({
                                applicationData: updateApplicationData,
                                eventLanguages: updateEventLanguages,
                            })
                        }
                    }).catch(response => {
                        this.error(response.message)
                    });
                };
            }).catch(response => {
                this.error(response.message)
            });
        };
    }


    // Del Tag
    deleteTag(tag_id, type) {
        let updateApplicationData = this.state.applicationData;

        if (type == "action") {
            tagList.remove({
                "tag_id": tag_id,
                "response_id": parseInt(this.props.match.params.id),
                "event_id": this.props.event.id
            }).then(response => {
                if (response.status == 200) {
                    updateApplicationData.tags.forEach((tag, index) => {
                        if (tag.id == tag_id) {
                            updateApplicationData.tags.splice(index, 1)
                        }
                    });
                    this.setState({
                        applicationData: updateApplicationData,
                    })
                };
            }).catch((response) => {
                this.error(response.message)
            });
        }
        else {
            this.setDeleteModal(tag_id, type)
        }
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
            };
            if (submitted) {
                return ["submitted" + " " + data.submitted_timestamp]
            };
            if (withdrawn) {
                return ["withdrawn" + " " + data.withdrawn_timestamp]
            };
        };
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
            });
        };

        return html
    }



    // Render Questions 
    renderQuestions(section) {
        let questions = section.questions.map(q => {
            return <div key={q.id} className="question-answer-block">
                <p>{q.headline}</p>
                <h6>{this.renderAnswer(q.id, q.type)}</h6>
            </div>
        });
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
            };
        });

        // format aswerers 
        function formatAnswer(a, type) {
            // file
            if (type == "file") {
                answers = <a className="answer file" key={a.value} target="_blank" href={baseUrl + "/api/v1/file?filename=" + a.value}>{a.value}</a>
            };
            // multi-file
            if (type == "multi-file") {
                let files = [];
                a.value.forEach((file => {
                    if (file) {
                        files.push(
                            <div key={a.headline}><a key={a.headline} target="_blank" href={baseUrl + "/api/v1/file?filename=" + file} className="answer">{a.value}</a></div>
                        )
                    }
                }));
                answers = <div key={a.headline}>{files}</div>
            };
            // choice
            if (type.includes("choice")) {
                let choices = [];
                a.options.forEach(opt => {
                    if (a.value == opt.value) {
                        choices.push(<div key={opt.label}><label className="answer">{opt.label}</label></div>)
                    };
                });
                answers = <div key={choices}>{choices}</div>
            };
            // text
            if (type.includes("text")) {
                answers = <div key={a.headline}><p className="answer">{a.value}</p></div>
            };
        };
        return answers
    }



    renderTags() {
        const data = this.state.applicationData;
        if (data) {
            let tags = data.tags.map(tag => {
                return <span
                    key={tag.id}
                    onClick={(e) => this.deleteTag(tag.id, "prompt")}
                    className="btn badge badge-info"
                    data-toggle="modal"
                    data-target="#exampleModal2"
                >
                    {tag.headline}
                    <i className="far fa-trash-alt"></i></span>
            });
            return tags
        };
    }



    renderTagModal() {
        const { eventLanguages } = this.state;
        if (eventLanguages) {
            return <TagModal
                keys={this.state.keys}
                i18nt={this.props.i18n}
                t={this.props.t}
                postTag={(tags) => this.postTag(tags, "tagList")}
                eventLanguages={eventLanguages}
            />
        };
    }



    renderDeleteModal() {
        const { eventLanguages } = this.state;
        if (eventLanguages) {
            return <DeleteModal
                t={this.props.t}
                handleSubmit={(tag_id, type) => this.deleteTag(tag_id, type)}
                deleteQue={this.state.deleteQue}
            />
        };
    }

    setDeleteModal(tag_id, type) {
        this.setState({
            deleteQue: type == "reset" ? null : tag_id
        })
    }


    render() {
        const { applicationData, tagList, tagMenu, error, eventLanguages } = this.state;
        const applicationStatus = this.applicationStatus();
        const renderSections = this.renderSections();
        const tags = this.renderTags();
        const tagModal = this.renderTagModal();
        const deleteModal = this.renderDeleteModal();
        // Translation
        const t = this.props.t;;

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
                                <span onClick={(e) => this.toggleTags(tagMenu)} className={tagMenu && tagList.length || tagMenu && eventLanguages.length
                                    ? "badge add-tags active"
                                    : "badge add-tags"}>
                                    Add tag
                            </span>
                            </div>

                            {/*Tag List*/}
                            <div className={tagMenu && tagList.length || tagMenu && eventLanguages.length
                                ? "tag-response show"
                                : "tag-response"}
                            >
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
                                                )} className="btn tag">{val.name}</button>
                                        </div>
                                    })}

                                <button data-toggle="modal" type="button" className="btn btn-primary" data-target="#exampleModal">
                                    {t('New tag')}
                                </button>


                            </div>
                        </div>

                        {/* User details Right Tab */}
                        <div>
                            <div className="user-details right"><label>{t('Application Status')}</label> <p>{applicationStatus}</p>
                                <button className="btn btn-primary" onClick={((e) => this.goBack(e))}>{t('Go Back')}</button>
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


