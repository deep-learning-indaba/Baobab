import React, { Component } from "react";
import { withRouter } from "react-router";

import FormTextArea from "../../../components/form/FormTextArea";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
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
        }

    }
    getDescription = (question) => {
        if (question.description) {
            return question.description;
        }
    }

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
                        this.setState({
                            questionSections: questionSections
                        });
                    }
                });
            });
        })
    }

    handleChange = event => {
        const value = event.target.value;
        if (this.props.onChange) {
            this.props.onChange(this.props.question, value);
        }
    };

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

    // submit = () => {
    //     let scores = this.state.questionModels.filter(qm => qm.score).map(qm => qm.score);
    //     if (this.isValidated()) {
    //         this.setState({
    //             isSubmitting: true
    //         }, () => {
    //             const shouldUpdate = this.state.form.review_response;
    //             reviewService
    //                 .submit(this.state.form.response.id, this.state.form.review_form.id, scores, shouldUpdate)
    //                 .then(response => {
    //                     if (response.error) {
    //                         this.setState({
    //                             error: response.error,
    //                             isSubmitting: false
    //                         });
    //                     }
    //                     else {
    //                         this.loadForm();
    //                     }
    //                 });
    //         })
    //     }
    // }

    render() {
        const {
            error,
            isLoading,
        } = this.state;

        const loadingStyle = {
            "width": "3rem",
            "height": "3rem"
        }

        this.formControl = (key, question, answer, validationError) => {
            switch (question.type) {
                case SHORT_TEXT:
                    return (
                        <FormTextBox
                            Id={this.id}
                            name={this.id}
                            type="text"
                            label={question.description}
                            placeholder={question.placeholder}
                            onChange={this.handleChange}
                            value={answer}
                            key={"i_" + key}
                            showError={validationError}
                            errorText={validationError}
                        />
                    );
                case SINGLE_CHOICE:
                    return (
                        <FormTextBox
                            Id={this.id}
                            name={this.id}
                            type="checkbox"
                            label={question.description}
                            placeholder={question.placeholder}
                            onChange={this.handleChange}
                            value={answer}
                            key={"i_" + key}
                            showError={validationError}
                            errorText={validationError}
                        />
                    );
                case LONG_TEXT[0]:
                case LONG_TEXT[1]:
                    return (
                        <FormTextArea
                            Id={this.id}
                            name={this.id}
                            label={question.description}
                            placeholder={question.placeholder}
                            onChange={this.handleChange}
                            value={answer}
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
                            id={this.id}
                            name={this.id}
                            label={question.description}
                            placeholder={question.placeholder}
                            onChange={this.handleChangeDropdown}
                            defaultValue={answer || null}
                            key={"i_" + key}
                            showError={validationError}
                            errorText={validationError}
                        />
                    );
                case FILE:
                    return (
                        <FormFileUpload
                            Id={this.id}
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
                {this.state.questionSections.length > 0 ? (
                    <div >
                        {console.log(this.state.questionSections)}
                        {this.state.questionSections.map(section => (
                            <div class="card">
                                <div>{section.name}</div>
                                <div>{section.description}</div>
                                {section.registration_questions.map(question => (
                                    <div>
                                        {this.formControl(
                                            question.id,
                                            question,
                                            ""
                                        )}

                                    </div>
                                ))}
                            </div>

                        ))}
                    </div>
                ) : (
                        <div class="alert alert-danger">No registration form available</div>
                    )}
            </div>
        )
    }
}

export default withRouter(RegistrationComponent);