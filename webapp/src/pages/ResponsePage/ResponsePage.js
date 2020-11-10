import React, { Component } from 'react'
import "react-table/react-table.css";
import './ResponsePage.css'
import { withTranslation } from 'react-i18next';
import ReviewModal from './components/ReviewModal';
import TagModal from './components/TagModal';
import { eventService } from '../../services/events/events.service';
import { applicationFormService } from '../../services/applicationForm/applicationForm.service';
import { reviewService } from '../../services/reviews/review.service';
import { tagsService } from '../../services/tags/tags.service';
import { responsesService } from '../../services/responses/responses.service';
import Loading from "../../components/Loading";
import { ConfirmModal } from "react-bootstrap4-modal";


class ResponsePage extends Component {
    constructor(props) {
        super(props);
        this.state = {
            mockReviews: [{ "reviewer_user_id": 4, "user_title": "Mr", "firstname": "Joe", "lastname": "Soap", "completed": false },
                { "reviewer_user_id": 3, "user_title": "Mr", "firstname": "Joe", "lastname": "Soap", "completed": false },
                null
            ],
            tagMenu: false,
            error: false,
            addNewTags: [],
            eventLanguages: [],
            isLoading: true,
            removeModalVisible: false
        }
    };

    componentDidMount() {

            Promise.all([
                eventService.getEvent(this.props.event.id),
                applicationFormService.getForEvent(this.props.event.id),
                responsesService.getResponseDetail(this.props.match.params.id, this.props.event.id),
                tagsService.getTagList(this.props.event.id),
                reviewService.getReviewAssignments(this.props.event.id)
            ]).then(responses => {
                console.log(responses);
                    this.setState({
                    eventLanguages: responses[0].event ? Object.keys(responses[0].event.name) : null,
                    applicationForm: responses[1].formSpec,
                    applicationData: responses[2].detail,
                    tagList: responses[3].tags,
                    reviewers: responses[4].reviewers,
                    error: responses[0].error || responses[1].error || responses[2].error || responses[3].error,
                    isLoading: false
                }, this.handleData);
            });
    }


    // Misc Functions
    // Go Back
    goBack() {
        this.props.history.goBack();
    }

    error(error) {
        this.setState({
            error: error
        })
    }

    // Toggle Tag Menu
    toggleTags(list) {
        this.setState({
            tagMenu: list ? false : true
        })
    }

    // Post Response API
    postResponseTag(tagId, responseId, eventId) {
        const updateApplicationData = this.state.applicationData;
        const updateTagList = this.state.tagList;

        responsesService.tagResponse(responseId, tagId, eventId)
            .then(response => {
                console.log(response)
                if (response.status == 201) {
                    const getTag = this.state.tagList.find(t => t.id === response.responseTag.tag_id);
                    updateApplicationData.tags.push({ "name": getTag.name, "id": getTag.id });
                    updateTagList.splice(getTag, 1);

                    this.setState({
                        applicationData: updateApplicationData,
                        tagList: updateTagList
                    });
                }
                else {
                    this.error(response.error);
                }
            });
    }

    // Post Tag List API
    addTag = (tagTranslations) => {
        if (Object.keys(tagTranslations).length) {
            const newTag = {
                name: tagTranslations
            };
            tagsService.addTag(newTag, this.props.event.id).then(response => {
                if (response.status == 201) {
                    const updateTagList = this.state.tagList;
                    const newTag = {
                        id: response.tag.id,
                        name: response.tag.name[this.props.i18n.language]
                    };
                    updateTagList.push(newTag);
                    this.setState({
                        tagList: updateTagList
                    }, ()=>{
                        this.postResponseTag(response.tag.id, this.props.match.params.id, this.props.event.id);
                    });
                }
                else {
                    this.error(response.error);
                }
            });
        };
    }

    // Del Tag
    removeTag(tag_id) {
        this.setState({
            removeModalVisible: true,
            tagToRemove: tag_id
        });
    }

    confirmRemoveTag = () => {
        const updateApplicationData = this.state.applicationData;

        responsesService.removeTag(
            parseInt(this.props.match.params.id),
            this.state.tagToRemove,
            this.props.event.id
        ).then(response => {
            if (response.status == 200) {
                const index = updateApplicationData.tags.findIndex(t => t.id === this.state.tagToRemove);
                if (index >= 0)
                    updateApplicationData.tags.splice(index, 1);
                
                this.setState({
                    applicationData: updateApplicationData,
                    removeModalVisible: false,
                    tagToRemove: null
                });
            }
            else {
                this.cancelRemoveTag();
                this.error(response.message);
            }
        });    
    }

    cancelRemoveTag = () => {
        this.setState({
            tagToRemove: null,
            removeModalVisible: false
        });
    }

    // Render Page HTML
    // Generate Applciation Status
    applicationStatus() {
        const data = this.state.applicationData;
        if (data) {
            const unsubmitted = !data.is_submitted && !data.is_withdrawn;
            const submitted = data.is_submitted;
            const withdrawn = data.is_withdrawn;

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
        const questions = section.questions.map(q => {
            if (q.type === "information") {
                return <h4>{q.headline}</h4>
            }
            return <div key={q.id} className="question-answer-block">
                <p>{q.headline}</p>
                <h6>{this.renderAnswer(q.id, q.type, q.headline, q.options)}</h6>
            </div>
        });
        return questions
    }


    // Render Reviews
    renderReviews() {
        const styles = {
            green: { "color": "green" },
            red: { "color": "red" }
        }
        
            if (this.state.mockReviews) {
                const reviews = this.state.mockReviews.map((val, index) => {
                    let num = parseInt(index) + 1;
                //   {"reviewer_user_id": 4, "user_title": "Mr", "firstname": "Joe", "lastname": "Soap", "completed": false},
                if (!val) {
                    return <div className="add-reviewer">
                        <button
                            data-toggle="modal"
                            type="button"
                            data-target="#exampleModalReview"
                            className="btn btn-light">
                            Assign Reviewer
                            </button>
                    </div>
                }
                else {
                    return <div className="reviewer">
                        <label>{"Reviewer" + num }</label>
                        <span>{val.user_title} {val.firstname} {val.lastname}</span>
                        {val.completed ? <p style={styles.green}>Completed</p> : <p style={styles.red}>Incomplete</p>}
                    </div>
                }
            })

           // console.log(reviews)

            return reviews
        }
    
    }



    // Render Answers 
    renderAnswer(id, type, headline, options) {
        const applicationData = this.state.applicationData;
        const baseUrl = process.env.REACT_APP_API_URL;

        const a = applicationData.answers.find(a => a.question_id === id);
        if (! a) {
            return this.props.t("No answer provided.");
        }
        else {
            // file
            if (type == "file") {
                return <a className="answer file" key={a.value} target="_blank" href={baseUrl + "/api/v1/file?filename=" + a.value}>{this.props.t("Uploaded File")}</a>
            }
            // multi-file
            else if (type == "multi-file") {
                const answerFiles = JSON.parse(a.value);
                let files = [];
                if (Array.isArray(answerFiles) && answerFiles.length > 0) {
                    files = answerFiles.map(file => <div key={file.name}><a key={file.name} target="_blank" href={baseUrl + "/api/v1/file?filename=" + file.file}>{file.name}</a></div>)
                }
                else {
                    files = "No files uploaded";
                }
                return <div key={headline}>{files}</div>
            }
            // choice
            else if (type.includes("choice")) {
                let choices = [];
                options.forEach(opt => {
                    if (a.value == opt.value) {
                        choices.push(<div key={opt.label}><label className="answer">{opt.label}</label></div>)
                    };
                });
                return <div key={choices}>{choices}</div>
            }
            // other
            else {
                return <div key={headline}><p className="answer">{a.value}</p></div>
            };
        }
    }


    renderTags() {
        const data = this.state.applicationData;
        if (data) {
            let tags = data.tags ? data.tags.map(tag => {
                return <span
                    key={tag.id}
                    className="btn badge badge-info"
                >
                    {tag.name}
                    <i onClick={(e) => this.removeTag(tag.id)} className="far fa-trash-alt"></i></span>
            })
                :
                null
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


        // Render Review Modal
        renderReviewerModal() {
            return < ReviewModal
             handlePost={(data) => this.postReviewer(data)}
                response={this.state.applicationData}
                reviewers={this.state.reviewers}
                event={this.props.event}
                t={this.props.t}
            />
        }
    
    
    
    postReviewer(data) {

        const updateReviews = this.state.mockReviews;

        const response = data.forEach(val => {
            return {
              "response_id": this.state.applicationData.id,    
              "event_id": this.props.event.id,
              "reviewer_user_id": val.email        
              }
        })  
        
        reviewService.assignReviewer(response).then(response => {
            if (response.status == 201) {
                data.forEach(val => {
                    updateReviews.unshift({
                        "reviewer_user_id": val.email, "user_title": val.email, "firstname": val.email, "lastname": val.email, "completed": false
                    })
                })

                this.setState({
                    mockReviews: updateReviews
                })
            }
        })
    }



    renderDeleteModal() {
        const t = this.props.t;

        return <ConfirmModal
          visible={this.state.removeModalVisible}
          onOK={this.confirmRemoveTag}
          onCancel={this.cancelRemoveTag}
          okText={t("Yes")}
          cancelText={t("No")}>
          <p>
            {t('Are you sure you want to delete this tag?')}
          </p>
        </ConfirmModal>
    }

    render() {
        const { applicationData, tagList, tagMenu, error, eventLanguages, isLoading } = this.state;
        // Translation
        const t = this.props.t;

        if (isLoading) {
            return <Loading/>
        }

        return (
            <div className="table-wrapper">
                {/* API Error */}
                {error &&
                    <div className="alert alert-danger" role="alert">
                        <p>{JSON.stringify(error)}</p>
                    </div>
                }

                {/* Add Tag Modal*/}
                {this.renderTagModal()}
                {this.renderDeleteModal()}
                {this.renderReviewerModal()}

                {/* Headings */}
                {applicationData &&
                    <div className="headings-lower">
                        <div className="user-details">
                            <h2>{applicationData.user_title} {applicationData.firstname} {applicationData.lastname}</h2>
                            <div className="tags">
                                {this.renderTags()}
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
                                                onClick={(e) => this.postResponseTag(
                                                        val.id,
                                                        parseInt(this.props.match.params.id),
                                                        this.props.event.id
                                                    )} className="btn tag">{val.name}</button>
                                        </div>
                                    })}

                                <button data-toggle="modal" type="button" className="btn btn-primary" data-target="#newTagModal">
                                    {t('New tag')}
                                </button>


                            </div>
                        </div>

                        {/* User details Right Tab */}
                        <div>
                            <div className="user-details right"><label>{t('Application Status')}</label> <p>{this.applicationStatus()}</p>
                                <button className="btn btn-primary" onClick={((e) => this.goBack(e))}>{t('Go Back')}</button>
                            </div>

                        </div>
                    </div>
                }



                {/*Response Data*/}
                {applicationData &&
                    <div className="response-details">
                        {/* Reviews */}
                        <div className="reviewers-section">
                            <h3>Reviewers</h3>
                            <div className="list">
                                {this.renderReviews()}
                            </div>

                            <div className="divider"></div>
                        </div>

                        {this.renderSections()}
                    </div>
                }

            </div>
        )
    }
}

export default withTranslation()(ResponsePage);
