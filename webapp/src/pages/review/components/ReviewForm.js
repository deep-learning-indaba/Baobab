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
                      value={score}
                      key={"i_" + key}
                      showError={validationError}
                      errorText={validationError}
                    />
                  );
            case INFORMATION:
                return (
                    <p>{answer && answer.value && answer.value.trim() 
                            ? <Linkify properties={{ target: '_blank' }}>{answer.value}</Linkify> 
                            : this.props.t("No Answer Provided")}
                    </p>
                )
            case FILE:
                return <div>
                    {answer && answer.value && answer.value.trim()
                        ? <a href={baseUrl + "/api/v1/file?filename=" + answer.value}>{this.props.t("View File")}</a>
                        : <p>{this.props.t("NO FILE UPLOADED")}</p>}
                </div>

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
        return "No Headline";
    }

    linkRenderer = (props) => <a href={props.href} target="_blank">{props.children}</a>

    renderHeader = (model) => {
        if (model.question.type === SECTION_DIVIDER) {
            return <div><hr/><h3>{this.getHeadline(model)}</h3></div>;
        }
        else if (model.question.type === INFORMATION || model.question.type === FILE || model.question.type === MULTI_FILE) {
            return <h5>{this.getHeadline(model)}</h5>;
        }
        else {
            return <h4>{this.getHeadline(model)}</h4>;
        }
    }

    render() {
        const className = (this.props.model.question.type === INFORMATION || this.props.model.question.type === FILE || this.props.model.question.type === MULTI_FILE)
            ? "question information" : "question";

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
            flagValue: ""
        }

    }

    processResponse = (response) => {
        let questionModels = null;

        if (!response.form.review_response || (response.form.review_response.id === 0 && !response.form.review_response.scores)) {
            response.form.review_response = null;
        }

        if (response.form && (response.form.reviews_remaining_count > 0 || response.form.review_response)) {
            questionModels = response.form.review_form.review_questions.map(q => {
                let score = null;
                if (response.form.review_response) {
                    score = response.form.review_response.scores.find(a => a.review_question_id === q.id)
                }
                return {
                    question: q,
                    answer: response.form.response.answers.find(a => a.question_id === q.question_id),
                    score: score
                };
            }).sort((a, b) => a.question.order - b.question.order);
        }

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
            flagValue: ""
        }, () => {
            window.scrollTo(0, 0);
        });
    }

    loadForm = (responseId) => {
        if (responseId) {
            reviewService.getReviewResponse(responseId)
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
        this.loadForm(id);
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

        this.setState({
            questionModels: newQuestionModels,
            validationStale: true
        });
    }

    validate = (questionModel, updatedScore) => {
        let errors = [];
        const question = questionModel.question;
        const score = updatedScore || questionModel.score;

        if (question.is_required && (!score || !score.value)) {
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

    isValidated = () => {
        const validatedModels = this.state.questionModels.map(q => {
            return {
                ...q,
                validationError: this.validate(q)
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

    submit = () => {
        let scores = this.state.questionModels.filter(qm => qm.score).map(qm => qm.score);
        if (this.isValidated()) {
            this.setState({
                isSubmitting: true
            }, () => {
                const shouldUpdate = this.state.form.review_response;
                reviewService
                    .submit(
                        this.state.form.response.id,
                        this.state.form.review_form.id,
                        scores,
                        shouldUpdate)
                    .then(response => {
                        if (response.error) {
                            this.setState({
                                error: response.error,
                                isSubmitting: false
                            });
                        }
                        else {
                            if (this.state.form.review_response) {
                                this.props.history.push(`/reviewHistory`)
                            }
                            else {
                                this.loadForm();
                            }
                        }
                    });
            })
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

        if (!form.review_response && form.reviews_remaining_count === 0) {
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

                <button
                    onClick={this.addFlag}
                    className="btn btn-light flag-category">
                    {t("Flag Response")} <i className="fa fa-flag"></i>
                </button>
                <hr />
                <div>
                    {t("Response ID")}: <span className="font-weight-bold">{form.response.id}</span> - {t("Please quote this in any correspondence with event admins outside of the system.")}
                </div>

                <hr />

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
                {!form.review_response &&
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
