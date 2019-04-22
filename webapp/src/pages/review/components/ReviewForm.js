import React, { Component } from "react";
import { withRouter } from "react-router";

import FormCheckbox from "../../../components/form/FormCheckbox";
import FormTextArea from "../../../components/form/FormTextArea";
import FormRadio from "../../../components/form/FormRadio";

import { reviewService } from "../../../services/reviews";
import { createColClassName } from "../../../utils/styling/styling";

import Linkify from 'react-linkify';

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

const LONG_TEXT = "long-text";
const RADIO = "multi-choice";  // TODO: Change backend to return "radio"
const INFORMATION = "information";
const CHECKBOX = "checkbox";

class ReviewQuestion extends Component {
    constructor(props) {
        super(props);
        this.id = "question_" + props.model.question.id;
    }

    handleChange = event => {
        const value =  event.target.type === 'checkbox' ? (event.target.checked | 0) : event.target.value;
        if (this.props.onChange) {
            this.props.onChange(this.props.model, value);
        }
    };

    getDescription = (question, answer) => {
        if (question.description) {
            return question.description;
        }

        if (answer && answer.value && answer.value.trim()) {
            return answer.value;
        }

        return "<No Answer Provided>";
    }

    formControl = (key, question, answer, score, validationError) => {
        switch (question.type) {
            case LONG_TEXT: 
                return (
                    <FormTextArea
                        Id={this.id}
                        name={this.id}
                        label={this.getDescription(question, answer)}
                        placeholder={question.placeholder}
                        onChange={this.handleChange}
                        value={score}
                        rows={5}
                        key={"i_" + key}
                        showError={validationError}
                        errorText={validationError}
                    />
                );
            case INFORMATION:
                return (
                    <p>{this.getDescription(question, answer)}</p>
                )
            case CHECKBOX:
                return (
                    <FormCheckbox
                        Id={this.id}
                        name={this.id}
                        label={this.getDescription(question, answer)}
                        placeholder={question.placeholder}
                        onChange={this.handleChange}
                        value={score}
                        key={"i_" + key}
                        showError={validationError}
                        errorText={validationError}
                    />
                )
            case RADIO:
                return (
                    <FormRadio
                        Id={this.id}
                        name={this.id}
                        label={this.getDescription(question, answer)}
                        onChange={this.handleChange}
                        options={question.options}
                        value={score}
                        key={"i_" + key}
                        showError={validationError}
                        errorText={validationError}
                    />
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

    render() {
        return (
          <div className={"question"}>
            <h4>{this.getHeadline(this.props.model)}</h4>
            <Linkify>
                {this.formControl(
                    this.props.model.question.id,
                    this.props.model.question,
                    this.props.model.answer,
                    this.props.model.score ? this.props.model.score.value : null,
                    this.props.model.validationError
                )}
            </Linkify>
          </div>
        )
    }
}

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
            currentSkip: 0
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
                    answer: response.form.response.answers.find(a => a.question_id == q.question_id),
                    score: score
                };
            }).sort((a, b) => a.question.order - b.question.order);
        }

        this.setState({
            form: response.form,
            error: response.error,
            isLoading: false,
            questionModels: questionModels,
            error: "",
            hasValidated: false,
            validationStale: false,
            isValid: false,
            isSubmitting: false
        }, ()=>{
            window.scrollTo(0, 0);
        });
    }

    loadForm = (responseId) => {
        if (responseId) {
            reviewService.getReviewResponse(responseId).then(this.processResponse);
        }
        else {
            reviewService.getReviewForm(DEFAULT_EVENT_ID, this.state.currentSkip).then(this.processResponse);
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
          errors.push("An answer/rating is required.");
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
        let scores = this.state.questionModels.filter(qm=>qm.score).map(qm=>qm.score);
        if (this.isValidated()) {
            this.setState({
                isSubmitting: true
            }, ()=> {
                const shouldUpdate = this.state.form.review_response;
                reviewService
                    .submit(this.state.form.response.id, this.state.form.review_form.id, scores, shouldUpdate)
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

        if (!form.review_response && form.reviews_remaining_count == 0) {
            return (
                <div class="review-form-container">
                    <div class="alert alert-success">
                        <p class="complete-title">All Done!</p><br/>
                        You have completed all your reviews! Please let us know if you have any capacity for more :)
                        <br/><br/>
                        Thank you for your contribution to the Deep Learning Indaba!
                    </div>
                </div>
            )
        }

        return (
            <div class="review-form-container">
                <h3 class="text-center mb-4">{form.user.user_category}</h3>
                <div class="row">
                    <div className={createColClassName(12, 6, 3, 3)}>
                        <span class="font-weight-bold">Nationality:</span><br/> {form.user.nationality_country}
                    </div>
                    <div className={createColClassName(12, 6, 3, 3)}>
                        <span class="font-weight-bold">Residence:</span><br/> {form.user.residence_country}
                    </div>
                    <div className={createColClassName(12, 6, 3, 3)}>
                        <span class="font-weight-bold">Affiliation:</span><br/> {form.user.affiliation}
                    </div>
                    <div className={createColClassName(12, 6, 3, 3)}>
                        <span class="font-weight-bold">Field of Study / Department:</span><br/> {form.user.department}
                    </div>
                </div>
                {questionModels && questionModels.map(qm => 
                    <ReviewQuestion model={qm} key={"q_" + qm.question.id} onChange={this.onChange}/>)
                }

                <br/><hr/>
                <div>
                    Response ID: <span className="font-weight-bold">{form.response.id}</span> - Please quote this in any correspondence with Baobab admins.
                </div>
                <hr/>

                <div class="buttons">
                    {currentSkip > 0 && 
                        <button
                            disabled={form.review_response || isSubmitting} 
                            className={"btn btn-secondary " + (form.review_response ? "hidden" : "")} 
                            style={{marginRight: "1em"}}
                            onClick={this.goBack}>
                            Go Back
                        </button>
                    }
                    {currentSkip < form.reviews_remaining_count && 
                        <button 
                            disabled={form.review_response || isSubmitting} 
                            className={"btn btn-secondary " + (form.review_response ? "hidden" : "")} 
                            onClick={this.skip}>
                            Skip
                        </button>
                    }
                    <button disabled={isSubmitting} type="submit" class="btn btn-primary float-right" onClick={this.submit}>
                        {isSubmitting && (
                            <span
                                class="spinner-grow spinner-grow-sm"
                                role="status"
                                aria-hidden="true"
                            />
                        )}
                        Submit
                    </button>
                </div>
                
                {(hasValidated && !validationStale && !isValid) && 
                    <div class="alert alert-danger">
                        There are one or more validation errors, please correct before submitting.
                    </div>
                }

                {!form.review_response &&
                    <div class="alert alert-info">
                        <span class="fa fa-info-circle"></span> You have {form.reviews_remaining_count} reviews remaining
                    </div>
                }
            </div>
        )
    }
}

export default withRouter(ReviewForm);
