import React, { Component } from "react";
import MarkdownRenderer from "../../../components/MarkdownRenderer";
import { withRouter } from "react-router";

import AnswerValue from "../../../components/answerValue";
import FormCheckbox from "../../../components/form/FormCheckbox";
import FormMultiCheckbox from "../../../components/form/FormMultiCheckbox";
import FormTextArea from "../../../components/form/FormTextArea";
import FormRadio from "../../../components/form/FormRadio";
import FormTextBox from "../../../components/form/FormTextBox";

import { reviewService } from "../../../services/reviews";
import { userService } from "../../../services/user";

import { Link } from "react-router-dom";
import { ConfirmModal } from "../../../components/Modal";
import { Trans, withTranslation } from 'react-i18next'

const LONG_TEXT = "long-text";
const SHORT_TEXT = "short-text";
const RADIO = ["multi-choice", "radio"];  // TODO: Change backend to return "radio"
const INFORMATION = "information";
const CHECKBOX = "checkbox";
const MULTI_CHECKBOX = "multi-checkbox";
const FILE = "file";
const MULTI_FILE = "multi-file";
const SECTION_DIVIDER = "section-divider";
const HEADING = "heading";
const SUB_HEADING = "sub-heading";
const NUMERIC = "numeric-text";


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

    linkRenderer = (props) => <a href={props.href} target="_blank" rel="noopener noreferrer">{props.children}</a>

    formControl = (key, question, answer, score, validationError) => {
        const question_type = answer && answer.question_type === FILE ? FILE : question.type;
        switch (question_type) {
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
            case NUMERIC:
                return (
                    <FormTextBox
                      id={this.id}
                      name={this.id}
                      type="number"
                      placeholder={question.placeholder}
                      onChange={this.handleChange}
                      value={score || ""}
                      key={"i_" + key}
                      showError={validationError}
                      errorText={validationError}
                    />
                );
            case INFORMATION:
                return <p className="answer"><AnswerValue answer={answer} question={question} /></p>;
            case HEADING:
                return "";
            case FILE:
                return <div className="answer"><AnswerValue answer={answer} question={question} /></div>;
            case MULTI_FILE:
                return <div className="answer"><AnswerValue answer={answer} question={question} /></div>;
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
                        options={question.options}
                        onChange={this.handleChange}
                        key={"i_" + key}
                        showError={validationError}
                        errorText={validationError} />
                )
            case RADIO[0]:
            case RADIO[1]:
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

    linkRenderer = (props) => <a href={props.href} target="_blank" rel="noopener noreferrer">{props.children}</a>

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
        if (this.props.model.question.type === INFORMATION && !this.props.model.answer) {
            return <div></div>
        }

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

                {this.props.model.question.description && <MarkdownRenderer source={this.props.model.question.description}/>}

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
            console.log("Response.form:", response.form);
            questionModels = response.form.review_form.review_sections.map(s => {
                return {
                    headline: s.headline,
                    description: s.description,
                    id: s.id,
                    order: s.order,
                    questions: s.review_questions.map(q => {
                        let score = null;
                        if (response.form.review_response) {
                            score = response.form.review_response.scores.find(a => a.review_question_id === q.id);
                        }
                        return {
                            question: q,
                            answer: response.form.response.answers.find(a => a.question_id === q.question_id),
                            score: score
                        };
                    }).sort((a, b) => a.question.order - b.question.order)
                }
            }).sort((a, b) => a.order - b.order);
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
        return questionModels.flatMap(s => s.questions).reduce((acc, q) =>
            acc + (q.question.weight > 0 && q.score && parseFloat(q.score.value) ? parseFloat(q.score.value*q.question.weight) : 0)
        , 0);
    }

    onChange = (model, value) => {
        const newScore = {
            review_question_id: model.question.id,
            value: value
        };

        const newQuestionModels = this.state.questionModels.map(s => {
            return {
                ...s,
                questions: s.questions.map(q => {
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
                })
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
        const validatedModels = this.state.questionModels.map(s=>({
            ...s,
            questions: s.questions.map(q=>({
                ...q,
                validationError: this.validate(q, null, checkRequired)
            }))
        }));

        const isValid = !validatedModels.flatMap(s=>s.questions).some(v => v.validationError);

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
        const scores = this.state.questionModels.flatMap(s => s.questions).filter(qm => qm.score).map(qm => qm.score);
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
        let scores = this.state.questionModels.flatMap(s => s.questions).filter(qm => qm.score).map(qm => qm.score);
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

    linkRenderer = (props) => <a href={props.href} target="_blank" rel="noopener noreferrer">{props.children}</a>

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

        const t = this.props.t;
        const editMode = this.props.match.params && this.props.match.params.id > 0;

        if (isLoading) {
            return (
                <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            );
        }

        if (error) {
            return (
                <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
                    {error}
                </div>
            );
        }

        if (!editMode && form.reviews_remaining_count === 0) {
            return (
                <div className="w-full max-w-5xl mx-auto pt-6 text-left">
                    <div className="bg-green-50 text-green-800 border border-green-200 p-8 rounded-2xl shadow-sm space-y-4 text-center">
                        <p className="text-xl font-bold">{t("All Done!")}</p>
                        <p className="text-sm">
                            {t("You have completed all your reviews! Please let us know if you have any capacity for more")}
                        </p>
                        <p className="text-xs text-muted-foreground mt-4 font-semibold">
                            {t("Thank you for your contribution!")}
                        </p>
                    </div>
                </div>
            )
        }

        const reviewsRemainingCount = form.reviews_remaining_count;

        return (
            <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-6">
                {questionModels && questionModels.map(section =>
                    <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6" key={"s_" + section.id}>
                        {section.headline && <h2 className="text-xl font-bold text-foreground pb-2 border-b border-border/50">{section.headline}</h2>}
                        {section.description && <div className="text-sm text-muted-foreground"><MarkdownRenderer source={section.description} /></div>}
                        {section.questions && section.questions.map(qm => 
                            <ReviewQuestion
                                model={qm}
                                key={"q_" + qm.question.id}
                                onChange={this.onChange} />
                        )}
                    </div>
                )}

                <div className="bg-slate-50 border border-border rounded-xl p-6 flex flex-col md:flex-row justify-between items-center gap-4">
                    <div className="text-lg font-bold text-foreground">
                        {t("Total Score")}: <span className="text-primary font-black">{this.state.totalScore}</span>
                    </div>

                    <button
                        onClick={this.addFlag}
                        className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-xs font-semibold border border-border text-muted-foreground hover:bg-slate-100 bg-white transition-colors cursor-pointer"
                    >
                        <i className="fa fa-flag mr-1.5 text-warning"></i>
                        {t("Flag Response")}
                    </button>
                </div>

                <div className="text-xs text-muted-foreground bg-slate-50 border border-border/50 p-4 rounded-xl leading-relaxed italic">
                    {t("Response ID")}: <span className="font-semibold text-foreground">{form.response.id}</span> - {t("Please quote this in any correspondence with admins outside of the system.")}
                </div>

                {this.state.saveValidationFailed && (
                    <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-4">
                        <i className="fa fa-exclamation mr-1.5"/> {this.props.t("Please fix validation errors before saving")}
                    </div>
                )}

                {this.state.saveSuccess && (
                    <div className="bg-green-50 text-green-700 border border-green-200 p-4 rounded-xl text-sm flex justify-between items-center mt-4 w-full">
                        <span>{this.props.t("Saved successfully")}</span>
                        <Link to={`/${this.props.event.key}/reviewlist`} className="text-primary hover:underline font-semibold text-xs">
                            {this.props.t("Return to review list")} &rarr;
                        </Link>
                    </div>
                )}

                {this.state.saveError && (
                    <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-4">
                        <i className="fa fa-exclamation mr-1.5"/> {this.state.saveError}
                    </div>
                )}

                {(hasValidated && !validationStale && !isValid) && (
                    <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-4">
                        {t("There are one or more validation errors, please correct before submitting.")}
                    </div>
                )}

                {!editMode && (
                    <div className="bg-blue-50 text-blue-700 border border-blue-200 p-4 rounded-xl text-sm mt-4 text-center">
                        <span className="fa fa-info-circle mr-1.5"></span> <Trans i18nKey="reviewsRemaining">You have {{reviewsRemainingCount}} reviews remaining</Trans>
                    </div>
                )}

                <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-6 border-t border-border/50">
                    <div className="flex items-center gap-2">
                        {currentSkip > 0 && (
                            <button
                                disabled={form.review_response || isSubmitting}
                                className="inline-flex items-center justify-center px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors border border-border text-muted-foreground hover:bg-slate-50 disabled:opacity-50 cursor-pointer"
                                onClick={this.goBack}
                            >
                                {t("Go Back")}
                            </button>
                        )}
                        {currentSkip < form.reviews_remaining_count && (
                            <button
                                disabled={form.review_response || isSubmitting}
                                className="inline-flex items-center justify-center px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors border border-border text-muted-foreground hover:bg-slate-50 disabled:opacity-50 cursor-pointer"
                                onClick={this.skip}
                            >
                                {t("Skip")}
                            </button>
                        )}
                    </div>

                    <div className="flex items-center gap-2">
                        <button 
                            disabled={isSubmitting || !this.state.stale} 
                            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors border border-primary text-primary hover:bg-primary/5 disabled:opacity-50 cursor-pointer"
                            onClick={this.save}
                        >
                            {isSubmitting && (
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-1.5"></div>
                            )}
                            {t("Save for later")}
                        </button>

                        <button 
                            disabled={isSubmitting}
                            type="button"
                            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50 cursor-pointer"
                            onClick={this.submit}
                        >
                            {isSubmitting && (
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-1.5"></div>
                            )}
                            {t("Submit")}
                        </button>
                    </div>
                </div>

                <ConfirmModal
                    visible={this.state.flagModalVisible}
                    onOK={this.handleFlagOk}
                    onCancel={this.handleFlagCancel}
                    onClickBackdrop={this.handleFlagCancel}
                    disableButtons={this.state.flagSubmitting}
                    okText={"Submit"}
                    cancelText={"Cancel"}
                    title="Flag applicant category">

                    <div className="flagModal p-4 space-y-4">
                        <p>{t("If reviewing this response revealed an issue that should be considered if this candidate were accepted, please describe it below.")}</p>
                        <textarea
                            className="w-full border border-border rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                            value={this.state.flagValue}
                            rows="4"
                            onChange={this.flagOnChange}>
                        </textarea>
                        {this.state.flagError &&
                            <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-4">
                                {this.state.flagError}
                            </div>}
                    </div>
                </ConfirmModal>
            </div>
        )
    }
}

export default withRouter(withTranslation()(ReviewForm));
