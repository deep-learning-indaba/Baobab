// TODO: ADD TRANSLATION

import React, { Component } from "react";
import { withRouter } from "react-router";
import { Link } from "react-router-dom";
import MarkdownRenderer from "../../../components/MarkdownRenderer";
import FormTextArea from "../../../components/form/FormTextArea";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import FormSelectOther from "../../../components/form/FormSelectOther";
import FormCheckbox from "../../../components/form/FormCheckbox";
import FormMultiCheckbox from "../../../components/form/FormMultiCheckbox";
import FormMultiCheckboxOther from "../../../components/form/FormMultiCheckboxOther";
import FormDate from "../../../components/form/FormDate";
import { registrationService } from "../../../services/registration";
import { offerServices } from "../../../services/offer";
import FileUploadComponent from "../../../components/FileUpload";
import Loading from "../../../components/Loading";
import _ from "lodash";

const SHORT_TEXT = "short-text";
const SINGLE_CHOICE = "single-choice";
const LONG_TEXT = ["long-text", "long_text"];
const MULTI_CHOICE = "multi-choice";
const CHOICE_OTHER = "choice-with-other";
const MULTI_CHECKBOX = "multi-checkbox";
const MULTI_CHECKBOX_OTHER = "multi-checkbox-with-other";
const FILE = "file";
const DATE = "date";
const INFORMATION = "information";

class RegistrationComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      isLoading: true,
      form: null,
      error: "",
      hasValidated: false,
      isValid: false,
      validationStale: false,
      isSubmitting: false,
      offer: [],
      questionSections: [],
      uploadPercentComplete: 0,
      answers: [],
      registrationId: false,
      registrationFormId: false,
      formSuccess: false,
      formFailure: false,
      registrationNotAvailable: false
    };
  }

  resetPage() {
    this.componentDidMount();
    this.setState({
      formSuccess: false
    });
  }

  getDescription = question => {
    if (question.description) {
      return question.description;
    }
  };

  handleChange = (id, event) => {
    let value = null;
    if (event.target) {
      value = event.target.type === "checkbox"
        ? event.target.checked | 0
        : event.target.value;
    }
    else {
      value = event;
    }

    this.onChange(id, value);
  };

  onChange = (id, value) => {
    let answer = this.state.answers.find(
      a => a.registration_question_id === id);
    let answers = this.state.answers;

    if (answer) {
      answer.value = value.toString();
      answers = answers.map(function (item) {
        return item.registration_question_id === id ? answer : item;
      });
    } else {
      answer = {
        registration_question_id: parseInt(id),
        value: value.toString()
      };
      answers.push(answer);
    }

    this.setState({
      answers: answers
    }, () => {
      if (this.state.hasValidated) {
        this.isValidated();
      }
    }
    );
  };

  handleChangeDropdown = (id, dropdown) => {
    let value = dropdown.value.toString();
    this.onChange(id, value);
  };

  componentDidMount() {
    this.setState({ isLoading: true });

    offerServices.getOffer(this.props.event ? this.props.event.id : 0).then(result => {
      if (result.error === "" && result.offer !== null) {
        this.setState({
          offer: result.offer,
          error: result.error
        }, () => {
          registrationService
            .getRegistrationForm(this.props.event ?
              this.props.event.id : 0,
              this.state.offer.id)
            .then(result => {
              if (
                result.error === "" &&
                result.form.registration_sections.length > 0
              ) {
                let questionSections = [];
                for (var i = 0; i < result.form.registration_sections.length; i++) {
                  if (result.form.registration_sections[i].registration_questions.length > 0) {
                    questionSections.push(
                      result.form.registration_sections[i]);
                  }
                }

                registrationService.getRegistrationResponse(this.props.event ? this.props.event.id : 0)
                  .then(result => {
                    if (result.error === "") {
                      this.setState({
                        isLoading: false,
                        answers: result.form.answers,
                        registrationId: result.form.registration_id
                      });
                    } else {
                      this.setState({
                        isLoading: false
                      });
                    }
                  })
                  .catch(error => { });
                this.setState({
                  questionSections: questionSections.sort(
                    (a, b) => a.order - b.order),
                  registrationFormId: result.form.id,
                });
              } else {
                if (result.statusCode === 409) {
                  this.props.history.push("/offer");
                }
                if (result.statusCode === 404) {
                  this.setState({
                    registrationNotAvailable: true,
                    isLoading: false
                  });
                }
                else {
                  this.setState({
                    error: result.error,
                    isLoading: false
                  });
                }
              }
            });
        }
        );
      } else {
        this.setState({
          isLoading: false,
          error: result.error
        });
      }
    });
  }

  validate = (question, answer) => {
    if (question.depends_on_question_id) {
      let answer = _.find(this.state.answers, a => a.registration_question_id.toString() === question.depends_on_question_id.toString());
      if (answer && answer.value === question.hide_for_dependent_value) {
        return {
          registration_question_id: question.id,
          error: ""
        };
      }
    }

    let errors = [];

    if (question.is_required && (!answer || !answer.value)) {
      errors.push(question.validation_text || "An answer is required.");
    }

    if (answer &&
      question.validation_regex &&
      !answer.value.match(question.validation_regex)
    ) {
      errors.push(question.validation_text);
    }

    return {
      registration_question_id: question.id,
      error: errors.join("; ")
    };
  };

  isValidated = () => {
    const validationErrors = this.state.questionSections.flatMap(section =>
      section.registration_questions.map(question => {
        let answer = this.state.answers.find(
          a => a.registration_question_id === question.id
        );
        return this.validate(question, answer);
      })
    );

    const isValid = !validationErrors.some(v => v.error);

    this.setState({
      validationErrors: validationErrors,
      validationStale: false,
      isValid: isValid
    });

    return isValid;
  };

  buttonSubmit = e => {
    e.preventDefault();

    let data = {
      registration_id: this.state.registrationId,
      offer_id: this.state.offer.id,
      registration_form_id: this.state.registrationFormId,
      answers: this.state.answers
    };

    this.setState({
      hasValidated: true
    });

    if (this.isValidated()) {
      this.setState({
        isSubmitting: true
      }, () => {
        registrationService.submitResponse(
          data,
          this.state.registrationId ? true : false)
          .then(response => {
            if (response.error === "" &&
              (response.form.status === 201 || response.form.status === 200)
            ) {
              this.setState({
                formFailure: false,
                formSuccess: true,
                isSubmitting: false
              });
            } else {
              this.setState({
                formFailure: true,
                formSuccess: false,
                isSubmitting: false,
                error: response.error
              });
            }
          })
          .catch(error => {
            this.setState({
              formFailure: true,
              formSuccess: false,
              isSubmitting: false
            });
          });
      }
      );
    }
  };

  render() {
    const {
      error,
      isLoading,
      hasValidated,
      validationStale,
      isValid,
      isSubmitting,
      registrationNotAvailable
    } = this.state;

    this.getDropdownDescription = (options, answer) => {
      return options.map(item => {
        if (item.value === answer.value) return item.label;
        return null;
      });
    };

    this.formControl = (key, question, answer, validError) => {
      let validationError = validError ? validError.error : "";

      switch (question.type) {
        case SHORT_TEXT:
          return (
            <FormTextBox
              id={`control_${question.id}`}
              name={`control_${question.id}`}
              type="text"
              label={question.description}
              value={answer ? answer.value : answer}
              placeholder={question.placeholder}
              onChange={e => this.handleChange(question.id, e)}
              key={"i_" + key}
              showError={validationError}
              errorText={validationError}
              required={question.is_required} />
          );
        case SINGLE_CHOICE:
          return (
            <FormCheckbox
              id={`control_${question.id}`}
              name={`control_${question.id}`}
              type="checkbox"
              label={question.description}
              placeholder={question.placeholder}
              onChange={e => this.handleChange(question.id, e)}
              value={answer ? parseInt(answer.value) : answer}
              key={"i_" + key}
              showError={validationError}
              errorText={validationError}
              required={question.is_required} />
          );
        case LONG_TEXT[0]:
        case LONG_TEXT[1]:
          return (
            <FormTextArea
              id={`control_${question.id}`}
              name={`control_${question.id}`}
              label={question.description}
              onChange={e => this.handleChange(question.id, e)}
              placeholder={question.placeholder}
              value={(answer && answer.value) || null}
              rows={5}
              key={"i_" + key}
              showError={validationError}
              errorText={validationError} />
          );
        case MULTI_CHOICE:
          return (
            <FormSelect
              options={question.options}
              id={`control_${question.id}`}
              name={`control_${question.id}`}
              onChange={(_, d) => this.handleChangeDropdown(question.id, d)}
              defaultValue={(answer && answer.value) || ""}
              placeholder={question.placeholder}
              label={question.description}
              required={question.is_required && !answer}
              key={"i_" + key}
              showError={validationError}
              errorText={validationError} />
          );
          case CHOICE_OTHER:
            return (
              <FormSelectOther
                options={question.options}
                id={`control_${question.id}`}
                name={`control_${question.id}`}
                onChange={e => this.onChange(question.id, e)}
                defaultValue={(answer && answer.value) || ""}
                placeholder={question.placeholder}
                label={question.description}
                required={question.is_required && !answer}
                key={"i_" + key}
                showError={validationError}
                errorText={validationError} />
            );
        case MULTI_CHECKBOX:
          return (
            <FormMultiCheckbox
              id={`control_${question.id}`}
              name={`control_${question.id}`}
              options={question.options}
              onChange={e => this.onChange(question.id, e)}
              defaultValue={(answer && answer.value) || ""}
              key={"i_" + key}
              showError={validationError}
              errorText={validationError} />
          )
        case MULTI_CHECKBOX_OTHER:
          return (
            <FormMultiCheckboxOther
              id={`control_${question.id}`}
              name={`control_${question.id}`}
              options={question.options}
              onChange={e => this.onChange(question.id, e)}
              defaultValue={(answer && answer.value) || ""}
              key={"i_" + key}
              showError={validationError}
              errorText={validationError} />
          )
        case FILE:
          return (
            <FileUploadComponent
              id={`control_${question.id}`}
              name={`control_${question.id}`}
              description={question.description}
              value={answer && answer.value}
              validationError={validationError}
              onChange={(_, v) => this.onChange(question.id, v)}
              key={"i_" + key} />
          );
        case DATE:
          return (
            <FormDate
              id={`control_${question.id}`}
              name={`control_${question.id}`}
              label={question.description}
              value={answer ? answer.value : answer}
              placeholder={question.placeholder}
              onChange={e => this.handleChange(question.id, e)}
              key={"i_" + key}
              showError={validationError}
              errorText={validationError}
              required={question.is_required} />
          );
        case INFORMATION:
          return question.description && <div className="application-form-information">{question.description}</div>
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
        <Loading />
      );
    }

    if (error) {
      return <div className={"alert alert-danger alert-container"}>
        {error}
      </div>;
    }

    if (registrationNotAvailable) {
      return <div className={"alert alert-warning alert-container"}>
        Thank you! Your confirmation has been recorded and your place is confirmed. We will contact you by email when the event registration form is available.
      </div>;
    }

    return (
      <div className="registration container-fluid pad-top-30-md">
        {this.state.formSuccess ? (
          <div>
            <div className="card flat-card success stretched">
              <h5>Successfully Registered</h5>
              <p>We look forward to welcoming you at {this.props.event.name}! You can now generate an <Link to={`/${this.props.event.key}/invitationLetter`}>invitation letter</Link> if you require one.</p>
            </div>
            <br/><br/>
            <div className="col-12">
              <button
                type="button"
                class="btn btn-primary"
                onClick={() => this.resetPage()}>
                Edit Answers
              </button>
            </div>
          </div>
        ) : (
            <div
              className={this.state.formSuccess ? "display-none" : "stretched"}>
              <h2>Registration</h2>
            </div>
          )}

        {this.state.formFailure && (
          <div className="alert alert-danger stretched alert-container">
            <div>{this.state.error}, please try again</div>
          </div>
        )}

        {this.state.registrationId && !this.state.formSuccess && (
          <div class="alert alert-success alert-container">
            You have already registered, but feel free to update your answers
            below if they've changed!
          </div>
        )}

        {this.state.questionSections.length > 0 &&
          !this.state.formSuccess ? (
            <div>
              {this.state.questionSections.map(section => (
                <div class="card stretched" key={"section_" + section.id}>
                  <h3>{section.name}</h3>
                  <div className="padding-v-15 mb-4 text-left registration-section-description">
                      <MarkdownRenderer children={section.description}/>
                  </div>

                  {section.registration_questions
                    .sort((a, b) => a.order - b.order)
                    .filter(question => {
                      if (question.depends_on_question_id) {
                        let answer = _.find(this.state.answers, a => a.registration_question_id.toString() === question.depends_on_question_id.toString());
                        return answer && (answer.value !== question.hide_for_dependent_value)
                      }
                      return true
                    })
                    .map(question => {
                      return (
                        <div
                          className="registration-question"
                          key={"question_" + question.id}>                            
                          <h5 className="form-label">{question.is_required && <span className="required-indicator">*</span>}{question.headline}</h5>
                          {this.formControl(
                            question.id,
                            question,
                            this.state.answers &&
                            this.state.answers.find(
                              a => a.registration_question_id === question.id
                            ),
                            this.state.validationErrors &&
                            this.state.validationErrors.find(
                              v => v.registration_question_id === question.id
                            )
                          )}
                        </div>
                      );
                    })}
                </div>
              ))}

              <button
                type="submit"
                class="btn btn-primary margin-top-32"
                onClick={this.buttonSubmit}>
                {isSubmitting && (
                  <span
                    class="spinner-grow spinner-grow-sm"
                    role="status"
                    aria-hidden="true" />
                )}
                Submit reponse
            </button>

              {hasValidated && !validationStale && !isValid && (
                <div class="alert alert-danger alert-container">
                  There are one or more validation errors, please correct before submitting.
                </div>
              )}
            </div>
          ) : (
            <div>
              {this.state.formSuccess !== true &&
                this.state.formFailure !== true && (
                  <div className="alert alert-danger alert-container">
                    Registration not available
                  </div>
                )}
            </div>
          )}
      </div>
    );
  }
}

export default withRouter(RegistrationComponent);
