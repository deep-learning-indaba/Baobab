import React, { Component } from "react";
import { withRouter } from "react-router";

import ReactMarkdown from "react-markdown";
import FormCheckbox from "../../../components/form/FormCheckbox";
import FormMultiCheckbox from "../../../components/form/FormMultiCheckbox";
import FormTextArea from "../../../components/form/FormTextArea";
import FormRadio from "../../../components/form/FormRadio";
import FormTextBox from "../../../components/form/FormTextBox";

import { reviewService } from "../../../services/reviews";
import { userService } from "../../../services/user";

import Linkify from 'react-linkify';
import { Link } from "react-router-dom";
import { ConfirmModal } from "react-bootstrap4-modal";
import { Trans, withTranslation } from 'react-i18next'

const LONG_TEXT = "long-text";
const SHORT_TEXT = "short-text";
const RADIO = "multi-choice";  // TODO: Change backend to return "radio"
const INFORMATION = "information";
const CHECKBOX = "checkbox";
const MULTI_CHECKBOX = "multi-checkbox";
const FILE = "file";
const MULTI_FILE = "multi-file";
const SECTION_DIVIDER = "section-divider";
const HEADING = "heading";
const SUB_HEADING = "sub-heading";

const baseUrl = process.env.REACT_APP_API_URL;

class ReviewQuestionComponent extends Component {
    constructor(props) {
        super(props);
        this.id = "question_" + props.model.question.id;
    }

    handleChange = event => {
        const value = event.target.type === 'checkbox' ? (event.target.checked | 0) : event.target.value;
        if (this.props.onChange) {
            this.props.onChange(this.props.model, value);
        }
    };

    linkRenderer = (props) => <a href={props.href} target="_blank">{props.children}</a>

    formControl = (key, question, answer, score, validationError) => {
        switch (question.type) {
            case LONG_TEXT:
                return (
                    <FormTextArea
                        id={this.id}
                        name={this.id}
                        placeholder={question.placeholder}
                        onChange={this.handleChange}
                        value={score}
                        rows={5}
                        key={"i_" + key}
                        showError={validationError}
                        errorText={validationError} />
                );
            case SHORT_TEXT:
                return (
                    <FormTextBox
                      id={this.id}
                      name={this.id}
                      type="text"
                      placeholder={question.placeholder}
                      onChange={this.handleChange}
                      value={score || ""}
                      key={"i_" + key}
                      showError={validationError}
                      errorText={validationError}
                    />
                  );
            case INFORMATION:
                if (answer && answer.type === "information") {
                    return "";
                }
                if (answer && answer.value && answer.value.trim()) {
                    return (
                        <p className="answer"><Linkify properties={{ target: '_blank' }}>{answer.value}</Linkify></p>
                    );
                }
                return <p className="answer">{this.props.t("No Answer Provided")}</p>
            case HEADING:
                return "";
            case FILE:
                return <div className="answer">
                    {answer && answer.value && answer.value.trim()
                        ? <div><a href={baseUrl + "/api/v1/file?filename=" + answer.value} target="_blank">{this.props.t("View File")}</a><br/><span className="small-text">*{this.props.t("Note: You may need to change the file name to open the file on certain operating systems")}</span></div>
                        : <p>{this.props.t("NO FILE UPLOADED")}</p>}
                </div>
            case MULTI_FILE:
                if (answer && answer.value) {
                    const answerFiles = JSON.parse(answer.value);
                    return <div className="answer">
                        {answerFiles.map((file, i) => <div><a key={file.name + `_${i}`} target="_blank" href={baseUrl + "/api/v1/file?filename=" + file.file}>{file.name}</a></div>)}
                        <br/>
                        <span className="small-text">*{this.props.t("Note: You may need to change the file name to open the file on certain operating systems")}</span>
                    </div> 
                }
                else {
                    return <p className="answer">{this.props.t("NO FILE UPLOADED")}</p>;
                }
                
            case CHECKBOX:
                return (
                    <FormCheckbox
                        id={this.id}
                        name={this.id}
                        placeholder={question.placeholder}
                        onChange={this.handleChange}
                        value={score}
                        key={"i_" + key}
                        showError={validationError}
                        errorText={validationError} />
                )
            case MULTI_CHECKBOX:
                return (
                    <FormMultiCheckbox
                        id={this.id}
                        name={this.id}
                        options={this.options}
                        onChange={this.handleChange}
                        key={"i_" + key}
                        showError={validationError}
                        errorText={validationError} />
                )
            case RADIO:
                return (
                    <FormRadio
                        id={this.id}
                        name={this.id}
                        onChange={this.handleChange}
                        options={question.options}
                        value={score}
                        key={"i_" + key}
                        showError={validationError}
                        errorText={validationError} />
                )
            case SECTION_DIVIDER:
                return (
                    <hr/>
                )
            case SUB_HEADING:
                return "";
            default:
                return (
                    <p className="text-danger">
                        WARNING: No control found for type {question.type}!
                    </p>
                );
        }
    }

    getHeadline = model => {
        if (model.question.headline) {
            return model.question.headline;
        }
        if (model.answer) {
            return model.answer.question;
        }
    }

    linkRenderer = (props) => <a href={props.href} target="_blank">{props.children}</a>

    renderHeader = (model) => {
        if (model.question.type === SECTION_DIVIDER) {
            return <div><hr/><h3>{this.getHeadline(model)}</h3></div>;
        }
        if (model.question.type === SUB_HEADING) {
            return <h3>{this.getHeadline(model)}</h3>
        }
        else if (model.question.type === INFORMATION || model.question.type === FILE || model.question.type === MULTI_FILE || model.question.type === HEADING) {
            return <h5>{this.getHeadline(model)}</h5>;
        }
        else {
            return <h4>{this.getHeadline(model)}</h4>;
        }
    }

    render() {
        let className = "question";
        if (this.props.model.question.type === INFORMATION || this.props.model.question.type === FILE || this.props.model.question.type === MULTI_FILE || this.props.model.question.type === HEADING) {
            className = className + " information";
        }
        else if (this.props.model.question.type !== SECTION_DIVIDER && this.props.model.question.type !== SUB_HEADING) {
            className = className + " review";
        }

        return (
            <div className={className}>
                {this.renderHeader(this.props.model)}

                {this.props.model.question.description && <ReactMarkdown source={this.props.model.question.description} renderers={{link: this.linkRenderer}}/>}

                {this.formControl(
                    this.props.model.question.id,
                    this.props.model.question,
                    this.props.model.answer,
                    this.props.model.score ? this.props.model.score.value : null,
                    this.props.model.validationError
                )}
            </div>
        )
    }
}

const ReviewQuestion = withTranslation()(ReviewQuestionComponent);

class ReviewForm extends Component {
    constructor(props) {
        super(props);

        this.state = {
            questionModels: null,
            isLoading: true,
            form: null,
            error: "",
            hasValidated: false,
            validationStale: false,
            isValid: false,
            isSubmitting: false,
            currentSkip: 0,
            flagModalVisible: false,
            flagValue: "",
            totalScore: 0,
            stale: false
        }

    }

    processResponse = (response) => {
        let questionModels = null;

        if (response.error) {
            this.setState({
                error: JSON.stringify(response.error),
                isLoading: false
            });
            return;
        }

        if (!response.form.review_response || (response.form.review_response.id === 0 && !response.form.review_response.scores)) {
            response.form.review_response = null;
        }

        if (response.form) {
            questionModels = response.form.review_form.review_questions.map(q => {
                let score = null;
                if (response.form.review_response) {
                    score = response.form.review_response.scores.find(a => a.review_question_id === q.id);
                }
                return {
                    question: q,
                    answer: response.form.response.answers.find(a => a.question_id === q.question_id),
                    score: score
                };
            }).sort((a, b) => a.question.order - b.question.order);
        }

        const totalScore = questionModels ? this.computeTotalScore(questionModels) : 0;

        this.setState({
            form: response.form,
            // error: response.error, duplicate key
            isLoading: false,
            questionModels: questionModels,
            error: "",
            hasValidated: false,
            validationStale: false,
            isValid: false,
            isSubmitting: false,
            flagModalVisible: false,
            flagValue: "",
            totalScore: totalScore,
            stale: false
        }, () => {
            window.scrollTo(0, 0);
        });
    }

    loadForm = (responseId) => {
        if (responseId) {
            reviewService.getResponseReview(responseId, this.props.event ? this.props.event.id : 0)
                .then(this.processResponse);
        } else {
            reviewService.getReviewForm(
                this.props.event ?
                    this.props.event.id : 0,
                this.state.currentSkip).then(this.processResponse);
        }
    }

    componentDidMount() {
        const { id } = this.props.match.params
        this.loadForm(id);  // NB: This is the RESPONSE (to the application form) id
    }

    computeTotalScore = (questionModels) => {
        return questionModels.reduce((acc, q) =>
            acc + (q.question.weight > 0 && q.score && parseFloat(q.score.value) ? parseFloat(q.score.value) : 0)
        , 0);
    }

    onChange = (model, value) => {
        const newScore = {
            review_question_id: model.question.id,
            value: value
        };

        const newQuestionModels = this.state.questionModels.map(q => {
            if (q.question.id !== model.question.id) {
                return q;
            }
            return {
                ...q,
                validationError: this.state.hasValidated
                    ? this.validate(q, newScore)
                    : "",
                score: newScore
            };
        });

        const totalScore = this.computeTotalScore(newQuestionModels);

        this.setState({
            questionModels: newQuestionModels,
            validationStale: true,
            totalScore: totalScore,
            stale: true,
            saveSuccess: false
        });
    }

    validate = (questionModel, updatedScore, checkRequired) => {
        let errors = [];
        const question = questionModel.question;
        const score = updatedScore || questionModel.score;

        if (checkRequired && question.is_required && (!score || !score.value)) {
            errors.push(this.props.t("An answer/rating is required."));
        }

        if (
            score &&
            question.validation_regex &&
            !score.value.match(question.validation_regex)
        ) {
            errors.push(question.validation_text);
        }
        return errors.join("; ");
    };

    isValidated = (checkRequired) => {
        const validatedModels = this.state.questionModels.map(q => {
            return {
                ...q,
                validationError: this.validate(q, null, checkRequired)
            };
        });

        const isValid = !validatedModels.some(v => v.validationError);

        this.setState(
            {
                questionModels: validatedModels,
                hasValidated: true,
                validationStale: false,
                isValid: isValid
            }
        );
        return isValid;
    };

    save = () => {
        const scores = this.state.questionModels.filter(qm => qm.score).map(qm => qm.score);
        if (this.isValidated(false)) {
            this.setState({
                isSubmitting: true,
                saveValidationFailed: false
            }, () => {
                const shouldUpdate = this.state.form.review_response;
                reviewService
                    .submit(
                        this.state.form.response.id,
                        this.state.form.review_form.id,
                        scores,
                        shouldUpdate,
                        false)
                    .then(response => {
                        if (response.error) {
                            this.setState({
                                error: response.error,
                                isSubmitting: false,
                                saveError: response.error
                            });
                        }
                        else {
                            this.setState({
                                saveSuccess: true,
                                stale: false,
                                isSubmitting: false,
                                form: {
                                    ...this.state.form,
                                    review_response: response.reviewResponse
                                }
                            });
                        }
                    });
            });
        }
        else {
            this.setState({
                saveValidationFailed: true
            });
        }
    }

    submit = () => {
        let scores = this.state.questionModels.filter(qm => qm.score).map(qm => qm.score);
        if (this.isValidated(true)) {
            this.setState({
                isSubmitting: true
            }, () => {
                const shouldUpdate = this.state.form.review_response;
                reviewService
                    .submit(
                        this.state.form.response.id,
                        this.state.form.review_form.id,
                        scores,
                        shouldUpdate,
                        true)
                    .then(response => {
                        if (response.error) {
                            this.setState({
                                error: response.error,
                                isSubmitting: false
                            });
                        }
                        else {
                            if (this.props.match.params && this.props.match.params.id > 0) {
                                this.props.history.push(`/${this.props.event.key}/reviewlist`)
                            }
                            else {
                                this.loadForm();
                            }
                        }
                    });
            });
        }
    }

    skip = () => {
        this.setState(prevState => {
            return {
                currentSkip: prevState.currentSkip + 1
            }
        }, () => {
            this.loadForm();
        });
    }

    goBack = () => {
        this.setState(prevState => {
            return {
                currentSkip: prevState.currentSkip - 1
            }
        }, () => {
            this.loadForm();
        });
    }

    handleFlagOk = () => {
        this.setState({
            flagSubmitting: true
        }, () => {
            userService.addComment(
                this.props.event ?
                    this.props.event.id : 0,
                this.state.form.user.id,
                this.state.flagValue)
                .then(response => {
                    if (response.error) {
                        this.setState({
                            flagError: response.error,
                            flagSubmitting: false
                        });
                    }
                    else {
                        this.setState({
                            flagError: "",
                            flagSubmitting: false,
                            flagModalVisible: false,
                            flagValue: ""
                        });
                    }
                });
        });
    }

    handleFlagCancel = () => {
        this.setState({
            flagModalVisible: false,
            flagValue: ""
        });
    }

    flagOnChange = event => {
        const value = event.target.value;
        this.setState({
            flagValue: value
        });
    }

    addFlag = event => {
        event.preventDefault();

        this.setState(prevState => {
            return {
                flagValue: "",
                flagModalVisible: true
            };
        });
    }

    render() {
        const {
            form,
            error,
            isLoading,
            questionModels,
            hasValidated,
            validationStale,
            isValid,
            isSubmitting,
            currentSkip
        } = this.state;

        const loadingStyle = {
            "width": "3rem",
            "height": "3rem"
        }

        const t = this.props.t;
        const editMode = this.props.match.params && this.props.match.params.id > 0;

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
            return <div className={"alert alert-danger alert-container"}>
                {error}
            </div>;
        }

        if (!editMode && form.reviews_remaining_count === 0) {
            return (
                <div class="review-form-container">
                    <div class="alert alert-success alert-container">
                        <p class="complete-title">{t("All Done!")}</p><br />
                        {t("You have completed all your reviews! Please let us know if you have any capacity for more")}
                        <br /><br />
                        {t("Thank you for your contribution!")}
                    </div>
                </div>
            )
        }

        const reviewsRemainingCount = form.reviews_remaining_count;

        return (
            <div class="review-form-container">
                {questionModels && questionModels.map(qm =>
                    <ReviewQuestion
                        model={qm}
                        key={"q_" + qm.question.id}
                        onChange={this.onChange} />
                )}
                <br /><hr />

                <div className="review-total-score">
                    {t("Total Score")}: {this.state.totalScore} 

                    <button
                        onClick={this.addFlag}
                        className="btn btn-light flag-category pull-right">
                        {t("Flag Response")} <i className="fa fa-flag"></i>
                    </button>
                    
                </div>

                <hr />
                <div>
                    {t("Response ID")}: <span className="font-weight-bold">{form.response.id}</span> - {t("Please quote this in any correspondence with admins outside of the system.")}
                </div>

                <hr />

                <div className="floating-bar">
                    <button disabled={isSubmitting} 
                        className={"btn btn-info"}
                        disabled={!this.state.stale}
                        onClick={this.save}>
                            {isSubmitting && (
                                <span
                                    class="spinner-grow spinner-grow-sm"
                                    role="status"
                                    aria-hidden="true"
                                />
                            )}
                            {t("Save for later")}
                    </button>

                    {this.state.saveValidationFailed && 
                        <span className="save-validation-failed text-danger">
                            <i class="fa fa-exclamation"/> {this.props.t("Please fix validation errors before saving")}
                        </span>
                    }

                    {this.state.saveSuccess && 
                        <span><span className="save-validation-failed text-success">{this.props.t("Saved")}</span><span className="return-to-list"><Link to={`/${this.props.event.key}/reviewlist`}>{this.props.t("Return to review list")}...</Link></span>
                        </span>
                    }

                    {this.state.saveError && 
                         <span className="save-validation-failed alert alert-danger">
                            <i class="fa fa-exclamation"/> {this.state.saveError}
                        </span>
                    }

                </div>

                <div class="buttons">
                    {currentSkip > 0 &&
                        <button
                            disabled={form.review_response || isSubmitting}
                            className={"btn btn-secondary " + (form.review_response ? "hidden" : "")}
                            style={{ marginRight: "1em" }}
                            onClick={this.goBack}>
                            {t("Go Back")}
                        </button>
                    }
                    {currentSkip < form.reviews_remaining_count &&
                        <button
                            disabled={form.review_response || isSubmitting}
                            className={"btn btn-secondary " + (form.review_response ? "hidden" : "")}
                            onClick={this.skip}>
                            {t("Skip")}
                        </button>
                    }
                    <button disabled={isSubmitting}
                        type="submit"
                        class="btn btn-primary float-right"
                        onClick={this.submit}>
                        {isSubmitting && (
                            <span
                                class="spinner-grow spinner-grow-sm"
                                role="status"
                                aria-hidden="true"
                            />
                        )}
                        {t("Submit")}
                    </button>
                </div>

                {(hasValidated && !validationStale && !isValid) &&
                    <div class="alert alert-danger alert-container">
                        {t("There are one or more validation errors, please correct before submitting.")}
                    </div>
                }
                <br />
                {!editMode &&
                    <div class="alert alert-info">
                        <span class="fa fa-info-circle"></span> <Trans i18nKey="reviewsRemaining">You have {{reviewsRemainingCount}} reviews remaining</Trans>
                    </div>
                }

                <ConfirmModal
                    visible={this.state.flagModalVisible}
                    onOK={this.handleFlagOk}
                    onCancel={this.handleFlagCancel}
                    onClickBackdrop={this.handleFlagCancel}
                    disableButtons={this.state.flagSubmitting}
                    okText={"Submit"}
                    cancelText={"Cancel"}
                    title="Flag applicant category">

                    <div class="flagModal">
                        <p>{t("If reviewing this response revealed an issue that should be considered if this candidate were accepted, please describe it below.")}</p>
                        <textarea
                            className="form-control"
                            value={this.state.flagValue}
                            rows="3"
                            onChange={this.flagOnChange}>
                        </textarea>
                        {this.state.flagError &&
                            <div class="alert alert-danger alert-container">
                                {this.state.flagError}
                            </div>}
                    </div>
                </ConfirmModal>
            </div>
        )
    }
}

export default withRouter(withTranslation()(ReviewForm));
