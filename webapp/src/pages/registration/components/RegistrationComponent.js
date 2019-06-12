import React, { Component } from "react";
import { withRouter } from "react-router";

import FormTextArea from "../../../components/form/FormTextArea";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import FormCheckbox from "../../../components/form/FormCheckbox";
import FormFileUpload from "../../../components/form/FormFileUpload";
import { registrationService } from "../../../services/registration";
import { fileService } from "../../../services/file/file.service";

import { ConfirmModal } from "react-bootstrap4-modal";

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

const SHORT_TEXT = "short-text";
const SINGLE_CHOICE = "single-choice";
const LONG_TEXT = ["long-text", "long_text"];
const MULTI_CHOICE = "multi-choice";
const FILE = "file";

class RegistrationComponent extends Component {
    constructor(props) {
        super(props);

        this.state = {
            isLoading: true,
            form: null,
            error: "",
            hasValidated: false,
            isValid: false,
            isSubmitting: false,
            offer: [],
            questionSections: [],
            uploadPercentComplete: 0,
            answers:[],
            registrationId:false,
            registrationFormId:false,
            formSucess:false,
            formFailure:false
        }

    }

    resetPage () {
        this.componentDidMount();
        this.setState({
             formSucess:false
        });
    }

    getDescription = (question) => {
        if (question.description) {
            return question.description;
        }
    }

    handleChange = event => {
        const value =  event.target.type === 'checkbox' ? (event.target.checked | 0) : event.target.value;
        var answers = this.state.answers;
        let id = event.target.id;

        var answer = answers.find(a => a.registration_question_id === id);
        if(answer)
        {
            answer.value = value.toString();
            answers = answers.map(function(item) { return item.registration_question_id == id ? answer : item; });
        }
        else{
            answer = {
                registration_question_id : parseInt(id),
                value : value.toString()
            }
            answers.push(answer);
        }
        this.setState({
            answers:answers
        }, () =>{
            console.log(this.state.answers);
        });

    };

    handleChangeDropdown = (id, dropdown) => {
        var answers = this.state.answers;

        var answer = answers.find(a => a.registration_question_id === id);
        if(answer)
        {
            answer.value = dropdown.value.toString();
            answers = answers.map(function(item) { return item.registration_question_id == id ? answer : item; });
        }
        else{
            answer = {
                registration_question_id : id.toString(),
                value : dropdown.value.toString()
            }
            answers.push(answer);
        }
        this.setState({
            answers:answers
        }, () =>{
            console.log(this.state.answers);
        });
      };
      

    componentDidMount() {
        registrationService.getOffer(DEFAULT_EVENT_ID).then(result => {
            this.setState({
                isLoading: false,
                offer: result.form,
                error: result.error
            }, () => {
                registrationService.getRegistrationForm(DEFAULT_EVENT_ID, this.state.offer.id).then(result => {
                    if (result.error == "" && result.form.registration_sections.length > 0) {
                        let questionSections = [];
                        for (var i = 0; i < result.form.registration_sections.length; i++) {
                            if (result.form.registration_sections[i].registration_questions.length > 0) {
                                questionSections.push(result.form.registration_sections[i]);
                            }
                        }
                        registrationService.getRegistrationResponse().then(result =>{
                            if(result.error === "")
                            {
                                this.setState({
                                    answers: result.form.answers,
                                    registrationId:result.form.registration_id
                                });
                            }

                        })
                        this.setState({
                            questionSections: questionSections,
                            registrationFormId:result.form.id
                        });
                    }
                });
            });
        })
    }

    

    handleUploadFile = (file) => {
        this.setState({
            uploading: true
        }, () => {
            fileService.uploadFile(file, progressEvent => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                this.setState({
                    uploadPercentComplete: percentCompleted
                });
            }).then(response => {
                if (response.fileId && this.props.onChange) {
                    this.props.onChange(this.props.question, response.fileId);
                }
                this.setState({
                    uploaded: response.fileId !== "",
                    uploadError: response.error,
                    uploading: false
                });
            })
        })
    }

    // validate = (questionModel, updatedScore) => {
    //     let errors = [];
    //     const question = questionModel.question;
    //     const score = updatedScore || questionModel.score;

    //     if (question.is_required && (!score || !score.value)) {
    //         errors.push("An answer is required.");
    //     }
    //     if (
    //         score &&
    //         question.validation_regex &&
    //         !score.value.match(question.validation_regex)
    //     ) {
    //         errors.push(question.validation_text);
    //     }

    //     return errors.join("; ");
    // };

    // isValidated = () => {
    //     const validatedModels = this.state.questionModels.map(q => {
    //         return {
    //             ...q,
    //             validationError: this.validate(q)
    //         };
    //     });

    //     const isValid = !validatedModels.some(v => v.validationError);

    //     this.setState(
    //         {
    //             questionModels: validatedModels,
    //             hasValidated: true,
    //             validationStale: false,
    //             isValid: isValid
    //         }
    //     );

    //     return isValid;
    // };

    buttonSubmit = () => {

        let data = {
            registration_id:this.state.registrationId,
            offer_id: this.state.offer.id,
            registration_form_id: this.state.registrationFormId,
            answers:this.state.answers
        }
        {
            this.setState({
                isLoading:true
            }, () => {
                registrationService.submitResponse(data,this.state.registrationId ? true : false).then(response => {
                    if(response.error === "" && response.form.status === 200)
                    {
                        this.setState({
                            formFailure:false,
                            formSucess:true,
                            isLoading:false
                        });
                    }
                    else{
                        this.setState({
                            formFailure:true,
                            formSucess:false,
                            isLoading:false
                        });
                    }
                }).catch(error => {
                    this.setState({
                        formFailure:true,
                        formSucess:false,
                        isLoading:false
                    });
                });
            });
        }
     }

    render() {
        const {
            error,
            isLoading,
        } = this.state;

        const loadingStyle = {
            "width": "3rem",
            "height": "3rem"
        }

        this.getDropdownDescription = (options,answer) =>{
            
            return options.map(item => {
                if(item.value == answer.value )
                return item.label;

            })
            return null;
        }

        this.formControl = (key, question, answer, validationError) => {
            switch (question.type) {
                case SHORT_TEXT:
                    return (
                        <FormTextBox
                            Id={question.id}
                            name={this.id}
                            type="text"
                            label={question.description}
                            placeholder={answer ? answer.value :question.placeholder}
                            onChange={this.handleChange}
                            key={"i_" + key}
                            showError={validationError}
                            errorText={validationError}
                            required={question.is_required && !answer}
                        />
                    );
                case SINGLE_CHOICE:
                    return (
                        <FormCheckbox
                        Id={question.id}
                            name={this.id}
                            type="checkbox"
                            label={question.description}
                            placeholder={question.placeholder}
                            onChange={this.handleChange}
                            value={answer ?  answer.value : answer}
                            key={"i_" + key}
                            showError={validationError}
                            errorText={validationError}
                        />
                    );
                case LONG_TEXT[0]:
                case LONG_TEXT[1]:
                    return (
                        <FormTextArea
                        Id={question.id}
                            name={this.id}
                            label={question.description}
                            placeholder={question.placeholder}
                            onChange={this.handleChange}
                            placeholder={answer ? answer.value : question.placeholder}
                            rows={5}
                            key={"i_" + key}
                            showError={validationError}
                            errorText={validationError}
                        />
                    );
                case MULTI_CHOICE:
                    return (
                        <FormSelect
                            options={question.options}
                            id={question.id}
                            onChange={this.handleChangeDropdown}
                            defaultValue={answer ? answer.label : ""}
                            placeholder={answer ? this.getDropdownDescription(question.options, answer)  :question.placeholder }
                            label={question.description}
                        />
                    );
                case FILE:
                    return (
                        <FormFileUpload
                        Id={question.id}
                            name={this.id}
                            label={question.description}
                            key={"i_" + key}
                            value={answer}
                            showError={validationError || this.state.uploadError}
                            errorText={validationError || this.state.uploadError}
                            uploading={this.state.uploading}
                            uploadPercentComplete={this.state.uploadPercentComplete}
                            uploadFile={this.handleUploadFile}
                            uploaded={this.state.uploaded}
                        />
                    );
                default:
                    return (
                        <p className="text-danger">
                            WARNING: No control found for type {question.type}!
          </p>
                    );
            }
        };

        if (isLoading) {
            return (
                <div class="d-flex justify-content-center">
                    <div class="spinner-border" style={loadingStyle} role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                </div>
            );
        }

        if (error) {
            return <div className={"alert alert-danger"}>{error}</div>;
        }

        return (
            <div className="registration container-fluid pad-top-30-md">
                <div className={this.state.formSucess ? "display-none":"stretched"}>
                    <h2>Registration</h2>
                </div>
                <div className={this.state.formSucess ? "card flat-card success stretched":"display-none"}>
                        <div >Sucesfully submitted</div>
                        <div className="col-12">
                        <button type="button"
                                class="btn btn-primary pull-right"
                                onClick={() => this.resetPage()}>Change your answers</button>
                        </div>
                </div>
                <div className={this.state.formFailure ? "alert alert-danger stretched":"display-none"}>
                        <div>Something went wrong, please try again</div>
                </div>
                {this.state.questionSections.length > 0 && !this.state.formSucess ? (
                    <form onSubmit={() => this.buttonSubmit()}>
                        {this.state.questionSections.map(section => (
                            <div class="card stretched">
                                <h3>{section.name}</h3>
                                <div className="padding-v-15">{section.description}</div>
                                
                                {section.registration_questions.map(question => (
                                    
                                    <div>
                                        {
                                        this.formControl(
                                        question.id,
                                        question,
                                        this.state.registrationId ? this.state.answers.find(a => a.registration_question_id === question.id) : null,
                                        ""
                                        )}
                                    </div>
                                ))}
                            </div>

                        ))}
                        <button
                            type="submit"
                            class="btn btn-primary stretched margin-top-32"
                            // onClick={() => this.buttonSubmit()}
                        >
                            Submit reponse
                </button>
                    </form>
                ) : (
                        <div className={this.state.formSucess != true && this.state.formFailure != true ? "alert alert-danger":"display-none"}>No registration form available</div>
                    )}
            </div>
        )
    }
}

export default withRouter(RegistrationComponent);