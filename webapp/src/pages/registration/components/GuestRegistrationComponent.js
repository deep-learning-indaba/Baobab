import React, { Component } from "react";
import { withRouter } from "react-router";

import FormTextArea from "../../../components/form/FormTextArea";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import FormCheckbox from "../../../components/form/FormCheckbox";
import FormFileUpload from "../../../components/form/FormFileUpload";
import { registrationService } from "../../../services/registration";
import { offerServices } from "../../../services/offer";
import { fileService } from "../../../services/file/file.service";

const DEFAULT_EVENT_ID = process.env.REACT_APP_DEFAULT_EVENT_ID || 1;

const SHORT_TEXT = "short-text";
const SINGLE_CHOICE = "single-choice";
const LONG_TEXT = ["long-text", "long_text"];
const MULTI_CHOICE = "multi-choice";
const FILE = "file";
const DATE = "date";

class FileUploadComponent extends Component {
  //TODO: Move to central place and share with application form
  constructor(props) {
    super(props);
    this.state = {
      uploadPercentComplete: 0,
      uploading: false,
      uploaded: false,
      uploadError: ""
    };
  }

  handleUploadFile = file => {
    this.setState(
      {
        uploading: true
      },
      () => {
        fileService
          .uploadFile(file, progressEvent => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            this.setState({
              uploadPercentComplete: percentCompleted
            });
          })
          .then(response => {
            if (response.fileId && this.props.onChange) {
              this.props.onChange(this.props.question.id, response.fileId);
            }
            this.setState({
              uploaded: response.fileId !== "",
              uploadError: response.error,
              uploading: false
            });
          });
      }
    );
  };

  render() {
    return (
      <FormFileUpload
        Id={this.props.question.id}
        name={this.id}
        label={this.props.question.description}
        key={"i_" + this.props.key}
        value={(this.props.answer && this.props.answer.value) || ""}
        showError={this.props.validationError || this.state.uploadError}
        errorText={this.props.validationError || this.state.uploadError}
        uploading={this.state.uploading}
        uploadPercentComplete={this.state.uploadPercentComplete}
        uploadFile={this.handleUploadFile}
        uploaded={this.state.uploaded}
      />
    );
  }
}

class GuestRegistrationComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      isLoading: false,
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
      formFailure: false
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

  handleChange = event => {
    const value =
      event.target.type === "checkbox"
        ? event.target.checked | 0
        : event.target.value;
    let id = parseInt(event.target.id);
    this.onChange(id, value);
  };

  onChange = (id, value) => {
    let answer = this.state.answers.find(
      a => a.registration_question_id === id
    );
    let answers = this.state.answers;
    if (answer) {
      answer.value = value.toString();
      answers = answers.map(function(item) {
        return item.registration_question_id == id ? answer : item;
      });
    } else {
      answer = {
        registration_question_id: parseInt(id),
        value: value.toString()
      };
      answers.push(answer);
    }
    this.setState(
      {
        answers: answers
      },
      () => {
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
    this.setState({isLoading: true});

    registrationService.getGuestRegistration(DEFAULT_EVENT_ID).then(result => {
      if (result.error == "" && result.form.registration_sections.length > 0) {
        let questionSections = [];
        for (var i = 0; i < result.form.registration_sections.length; i++) {
          if (
            result.form.registration_sections[i].registration_questions.length >
            0
          ) {
            questionSections.push(result.form.registration_sections[i]);
          }
        }
        registrationService
          .getGuestRegistrationResponse()
          .then(result => {
            if (result.error === "") {
              this.setState({
                isLoading: false,
                answers: result.form.answers,
                registrationId: result.form.guest_registration_id
              });
            }
            else {
              this.setState({
                isLoading: false
              });
            }
          })
          .catch(error => {});
        this.setState({
          questionSections: questionSections.sort((a, b) => a.order - b.order),
          registrationFormId: result.form.id,
        });
      } else {
        if (result.statusCode === 409) {
          this.props.history.push("/offer");
        }
        else {
          this.setState({
            isLoading: false,
            error: result.error
          });
        }
      }
    });
  }

  validate = (question, answer) => {
    let errors = [];

    if (question.is_required && (!answer || !answer.value)) {
      errors.push(question.validation_text || "An answer is required.");
    }
    if (
      answer &&
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
      guest_registration_id: this.state.registrationId,
      offer_id: this.state.offer.id,
      registration_form_id: this.state.registrationFormId,
      answers: this.state.answers
    };

    this.setState({
      hasValidated: true
    });

    if (this.isValidated()) {
      this.setState(
        {
          isSubmitting: true
        },
        () => {
          registrationService
            .submitGuestResponse(data, this.state.registrationId ? true : false)
            .then(response => {
              if (
                response.error === "" &&
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
      isSubmitting
    } = this.state;

    const loadingStyle = {
      width: "3rem",
      height: "3rem"
    };

    this.getDropdownDescription = (options, answer) => {
      return options.map(item => {
        if (item.value == answer.value) return item.label;
        return null;
      });
    };

    this.formControl = (key, question, answer, validError) => {
      let validationError = validError ? validError.error : "";
      switch (question.type) {
        case SHORT_TEXT:
          return (
            <FormTextBox
              Id={question.id}
              name={this.id}
              type="text"
              label={question.description}
              value={answer ? answer.value : answer}
              placeholder={question.placeholder}
              onChange={this.handleChange}
              key={"i_" + key}
              showError={validationError}
              errorText={validationError}
              required={question.is_required}
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
              value={answer ? parseInt(answer.value) : answer}
              key={"i_" + key}
              showError={validationError}
              errorText={validationError}
              required={question.is_required}
            />
          );
        case LONG_TEXT[0]:
        case LONG_TEXT[1]:
          return (
            <FormTextArea
              Id={question.id}
              name={this.id}
              label={question.description}
              onChange={this.handleChange}
              placeholder={answer ? answer.value : question.placeholder}
              value={answer ? answer.value : answer}
              rows={5}
              key={"i_" + key}
              showError={validationError}
              errorText={validationError}
              required={question.is_required && !answer}
            />
          );
        case MULTI_CHOICE:
          return (
            <FormSelect
              options={question.options}
              id={question.id}
              onChange={this.handleChangeDropdown}
              defaultValue={(answer && answer.value) || ""}
              placeholder={question.placeholder}
              label={question.description}
              required={question.is_required && !answer}
              key={"i_" + key}
              showError={validationError}
              errorText={validationError}
            />
          );
        case FILE:
          return (
            <FileUploadComponent
              question={question}
              answer={answer}
              validationError={validationError}
              onChange={this.onChange}
              key={"i_" + key}
            />
          );

        case DATE:
          return (
            <FormTextBox
              Id={question.id}
              name={this.id}
              type="date"
              label={question.description}
              value={answer ? answer.value : answer}
              placeholder={question.placeholder}
              onChange={this.handleChange}
              key={"i_" + key}
              showError={validationError}
              errorText={validationError}
              required={question.is_required}
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
        {this.state.formSuccess ? (
          <div className="card flat-card success stretched">
            <h5>Successfully Registered</h5>
            <p>We look forward to welcoming you at the Indaba!</p>
            <a href="/invitationLetter"> Request an invitation letter.</a>
            <div className="col-12">
              <button
                type="button"
                class="btn btn-primary pull-right"
                onClick={() => this.resetPage()}
              >
                Change your answers
              </button>
            </div>
          </div>
        ) : (
          <div
            className={this.state.formSuccess ? "display-none" : "stretched"}
          >
            <h2>Registration</h2>
          </div>
        )}
        {this.state.formFailure && (
          <div className="alert alert-danger stretched">
            <div>{this.state.error}, please try again</div>
          </div>
        )}
        {this.state.registrationId && !this.state.formSuccess && (
          <div class="alert alert-success">
            You have already registered, but feel free to update your answers
            below if they've changed!
          </div>
        )}
        {this.state.questionSections.length > 0 && !this.state.formSuccess ? (
          <div>
            {this.state.questionSections.map(section => (
              <div class="card stretched" key={"section_" + section.id}>
                <h3>{section.name}</h3>
                <div className="padding-v-15 mb-4 text-left">
                  {section.description}
                </div>

                {section.registration_questions
                  .sort((a, b) => a.order - b.order)
                  .map(question => {
                    if (question.depends_on_question_id) {
                      let answer = this.state.answers.find(
                        a =>
                          a.registration_question_id ==
                          question.depends_on_question_id
                      );
                      if (
                        !answer ||
                        answer.value == question.hide_for_dependent_value
                      ) {
                        return;
                      }
                    }
                    return (
                      <div
                        className="text-left"
                        key={"question_" + question.id}
                      >
                        <h5>{question.headline}</h5>
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
              onClick={this.buttonSubmit}
            >
              {isSubmitting && (
                <span
                  class="spinner-grow spinner-grow-sm"
                  role="status"
                  aria-hidden="true"
                />
              )}
              Submit reponse
            </button>
            {hasValidated && !validationStale && !isValid && (
              <div class="alert alert-danger">
                There are one or more validation errors, please correct before
                submitting.
              </div>
            )}
          </div>
        ) : (
          <div>
            {this.state.formSuccess !== true &&
              this.state.formFailure !== true && (
                <div className="alert alert-danger">
                  No registration form available
                </div>
              )}
          </div>
        )}
      </div>
    );
  }
}

export default withRouter(GuestRegistrationComponent);
