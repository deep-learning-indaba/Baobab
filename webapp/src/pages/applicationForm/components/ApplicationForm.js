import React, { Component, Fragment } from "react";
import { withRouter } from "react-router";
import { Link } from "react-router-dom";
import { applicationFormService } from "../../../services/applicationForm";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import FormTextArea from "../../../components/form/FormTextArea";
import FormDate from "../../../components/form/FormDate";
import MarkdownRenderer from "../../../components/MarkdownRenderer";
import FormMultiFile from '../../../components/form/FormMultiFile'
import ReactToolTip from "react-tooltip";
import { ConfirmModal } from "react-bootstrap4-modal";
import StepZilla from "react-stepzilla";
import FormFileUpload from "../../../components/form/FormFileUpload";
import { fileService } from "../../../services/file/file.service";
import FormMultiCheckbox from "../../../components/form/FormMultiCheckbox";
import FormReferenceRequest from "./ReferenceRequest";
import Loading from "../../../components/Loading";
import _ , { chain } from "lodash";
import { withTranslation } from 'react-i18next';
import AnswerValue from '../../../components/answerValue'
import FormSelectOther from "../../../components/form/FormSelectOther";
import FormMultiCheckboxOther from "../../../components/form/FormMultiCheckboxOther";
import FormCheckbox from "../../../components/form/FormCheckbox";
import { eventService } from "../../../services/events";
import moment from "moment";
import { Redirect } from 'react-router-dom';


const baseUrl = process.env.REACT_APP_API_URL;

const SHORT_TEXT = "short-text";
const SINGLE_CHOICE = "single-choice";
const LONG_TEXT = ["long-text", "long_text"];
const MULTI_CHOICE = "multi-choice";
const MULTI_CHECKBOX = "multi-checkbox";
const MULTI_CHOICE_OTHER = "multi-choice-other";
const MULTI_CHECKBOX_OTHER = "multi-checkbox-other";
const FILE = "file";
const DATE = "date";
const REFERENCE_REQUEST = "reference";
const INFORMATION = ['information', 'sub-heading']
const MULTI_FILE = 'multi-file';



/*
 * Utility functions for the feature where questions are dependent on the answers of other questions
 */
const isEntityDependentOnAnswer = (entityToCheck) => {
  return entityToCheck.depends_on_question_id && entityToCheck.show_for_values;
}

const findDependentQuestionAnswer = (entityToCheck, answers) => {
  return answers.find(a => a && a.question_id === entityToCheck.depends_on_question_id);
}

const doesAnswerMatch = (entityToCheck, answer) => {
  return entityToCheck.show_for_values.indexOf(answer.value) > -1;
}

const answerByQuestionKey = (key, allQuestions, answers) => {
  let question = allQuestions.find(q => q.key === key);
  if (question) {
    let answer = answers.find(a => a.question_id === question.id);
    if (answer) {
      return answer.value;
    }
  }
  return null;
}

class FieldEditor extends React.Component {
  constructor(props) {
    super(props);
    this.id = "question_" + props.question.id;
    this.state = {
      uploading: false,
      uploadPercentComplete: 0,
      uploadError: "",
      uploaded: false,
    }

  }

  handleChange = event => {
    // Some components (datepicker, custom controls) return pass the value directly rather than via event.target.value
    const value = event && event.target ? event.target.value : event;

    if (this.props.onChange) {
      this.props.onChange(this.props.question, value);
    }
  };

  handleCheckChange = event => {
    const value = event.target.checked;
    if (this.props.onChange) {
      this.props.onChange(this.props.question, value);
    }
  }

  handleChangeDropdown = (name, dropdown) => {
    if (this.props.onChange) {
      this.props.onChange(this.props.question, dropdown.value);
    }
  };

  handleUploadFile = (file) => {
    this.setState({
      uploading: true,
    })

    // TODO: Handle errors
    return fileService.uploadFile(file, progressEvent => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      this.setState({
        uploadPercentComplete: percentCompleted
      });
    }).then(response => {
      if (response.fileId && this.props.onChange) {
        this.props.onChange(
          this.props.question,
          JSON.stringify({ filename: response.fileId, rename: file.name })
        );
      }
      this.setState({
        uploaded: response.fileId !== "",
        uploadError: response.error,
        uploading: false
      });

      return response.fileId;
    });
  }

  formControl = (key, question, answer, validationError, responseId) => {

    switch (question.type) {
      case SHORT_TEXT:
        return (
          <FormTextBox
            id={this.id}
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
          <FormCheckbox
            id={this.id}
            name={this.id}
            label={question.description}
            placeholder={question.placeholder}
            onChange={this.handleCheckChange}
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
            id={this.id}
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
      case MULTI_CHOICE_OTHER:
        return (
          <FormSelectOther
            options={question.options}
            id={this.id}
            name={this.id}
            label={question.description}
            placeholder={question.placeholder}
            onChange={this.handleChange}
            defaultValue={answer || null}
            key={"i_" + key}
            showError={validationError}
            errorText={validationError}/>
        )
      case MULTI_CHECKBOX:
        return (
          <FormMultiCheckbox
            id={this.id}
            name={this.id}
            label={question.description}
            placeholder={question.placeholder}
            options={question.options}
            defaultValue={answer || null}
            onChange={this.handleChange}
            key={"i_" + key}
            showError={validationError}
            errorText={validationError} />
        )
        case MULTI_CHECKBOX_OTHER:
          return (
            <FormMultiCheckboxOther
              id={this.id}
              name={this.id}
              label={question.description}
              placeholder={question.placeholder}
              options={question.options}
              defaultValue={answer || ""}
              onChange={this.handleChange}
              key={"i_" + key}
              showError={validationError}
              errorText={validationError} />
          )
      case FILE:
        return (
          <FormFileUpload
            id={this.id}
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
            options={question.options}
          />
        );
      case DATE:
        return (
          <FormDate
            id={this.id}
            name={this.id}
            label={question.description}
            value={answer}
            placeholder={question.placeholder}
            onChange={this.handleChange}
            key={"i_" + key}
            showError={validationError}
            errorText={validationError}
            required={question.is_required}
          />
        );
      case MULTI_FILE:
        return (
          <FormMultiFile
            id={this.id}
            name={this.id}
            label={question.description}
            value={answer}
            onChange={this.handleChange}
            uploadFile={this.handleUploadFile}
            errorText={validationError || this.state.uploadError}
            placeholder={question.placeholder}
            options={question.options}
          />
        );
      case REFERENCE_REQUEST:
        return (
          <FormReferenceRequest
            id={this.id}
            name={this.id}
            label={question.description}
            value={answer}
            placeholder={question.placeholder}
            onChange={this.handleChange}
            key={"i_" + key}
            showError={validationError}
            errorText={validationError}
            required={question.is_required}
            options={question.options}
            responseId={responseId} />
        )
      case INFORMATION[0]:
      case INFORMATION[1]:
        return question.description && <div className="application-form-information">{question.description}</div>
      default:
        return (
          <p className="text-danger">
            WARNING: No control found for type {question.type}!
          </p>
        );
    }
  };

  render() {
    return (
      <div className={"question"}>
        <p className={INFORMATION.includes(this.props.question.type) ? "h3" : "h4"}>
          {this.props.question.is_required && <span className="required-indicator">*</span>}
          {this.props.question.headline}
        </p>
        {this.formControl(
          this.props.key,
          this.props.question,
          this.props.answer ? this.props.answer.value : null,
          this.props.validationError,
          this.props.responseId
        )}
      </div>
    );
  }
}

class Section extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      section: props.section,
      questionModels: props.questionModels
        .slice()
        .sort((a, b) => a.question.order - b.question.order),
      hasValidated: false,
      validationStale: false,

    };
  }


  onChange = (question, value) => {
    const newAnswer = {
      question_id: question.id,
      value: value
    };


    const newQuestionModels = this.state.questionModels
      .map(q => {
        if (q.question.id !== question.id) {
          return q;
        }
        return {
          ...q,
          validationError: this.state.hasValidated
            ? this.validate(q, newAnswer)
            : "",
          answer: newAnswer
        };
      })

    this.setState(
      {
        questionModels: newQuestionModels,
        validationStale: true
      },
      () => {
        if (this.props.changed) {
          this.props.changed();
        }
      }
    );
  };


  // validate
  validate = (questionModel, updatedAnswer) => {
    let errors = [];
    
    const question = questionModel.question;
    const answer = updatedAnswer || questionModel.answer;

    if (question.is_required && (!answer || !answer.value)) {
      errors.push(this.props.t("An answer is required."));
    }

    if (
      answer &&
      question.validation_regex &&
      !answer.value.match(question.validation_regex)
    ) {
      errors.push(question.validation_text);
    }

    return errors.join("; ");
  };


  // isValidated
  isValidated = () => {
    const allAnswersInSection = this.state.questionModels.map(q => q.answer);
    const validatedModels = this.state.questionModels
      .filter(q => this.dependentQuestionFilter(q.question, allAnswersInSection))
      .map(q => {
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
        validationStale: false
      },
      () => {
        if (this.props.answerChanged) {
          this.props.answerChanged(
            this.state.questionModels.map(q => q.answer).filter(a => a),
            isValid
          );
        }
      }
    );

    return isValid;
  };

  handleSave = () => {
    if (this.props.save) {
      this.props.save(
        this.state.questionModels.map(q => q.answer).filter(a => a)
      );
    }
  };

  /*
   * Only include questions that depend on other question's answers if they match.
   * If the value has been set, compare with that. If it hasn't been set, compare with the saved value.
   */
  dependentQuestionFilter = (question, sectionCurrentAnswers) => {
    if (isEntityDependentOnAnswer(question)) {
      const answer = findDependentQuestionAnswer(question, sectionCurrentAnswers);
      return answer ? doesAnswerMatch(question, answer) : this.props.showQuestionBasedOnSavedFormAnswers(question);
    } else {
      return true;
    }
  }

  render() {
    const {
      section,
      questionModels,
      hasValidated,
      validationStale
    } = this.state;

    const allAnswersInSection = questionModels.map(q => q.answer);

    return (
      <div className={"section"}>
        <div className={"headline"}>
          <h1>{section.name}</h1>
          <div className="description">
            <MarkdownRenderer children={section.description}/>
          </div>
        </div>
        {questionModels &&
          questionModels
            .filter(q => this.dependentQuestionFilter(q.question, allAnswersInSection))
            .map(model => (
              <FieldEditor
                key={"question_" + model.question.id}
                question={model.question}
                answer={model.answer}
                validationError={model.validationError}
                onChange={this.onChange}
                responseId={this.props.responseId}
              />
            )
            )
        }
        {this.props.unsavedChanges && !this.props.isSaving && (
          <button className="btn btn-secondary" onClick={this.handleSave} >
            {this.props.t("Save for later")}...
          </button>
        )}
        {this.props.isSaving && <span class="saving mx-auto">{this.props.t("Saving")}...</span>}
        {hasValidated && !validationStale && (
          <div class="alert alert-danger alert-container">
            {this.props.t("Please fix the errors before continuing.")}
          </div>
        )}
      </div>
    );
  }
}

class ConfirmationComponent extends React.Component {

  dependentQuestionFilter = (question, allAnswers) => {
    if (isEntityDependentOnAnswer(question)) {
      const answer = findDependentQuestionAnswer(question, allAnswers);
      return answer ? doesAnswerMatch(question, answer) : false;
    } else {
      return true;
    }
  }

  render() {
    const t = this.props.t;

    const allAnswers = this.props.sectionModels && this.props.sectionModels.flatMap(s=>s.questionModels.map(q=>q.answer));
    const allErrors = this.props.sectionModels 
      && this.props.sectionModels.flatMap(s=>s.questionModels.filter(qm => this.dependentQuestionFilter(qm.question, allAnswers)).map(q=>q.validationError)).filter(e=>e);

    return (
      <div>
        <div class="row">
          <div class="col confirmation-heading">
            <h2>{t("Review your Answers")}</h2>
            <p>
              {t("applicationConfirmationText")}
            </p>

            <div class="alert alert-warning">
              <span class="fa fa-exclamation-triangle"></span> {t("You MUST click SUBMIT before the deadline for your application to be considered!")}
            </div>

            <div class="text-center">
              {allErrors.length > 0 && <div class="alert alert-danger alert-container">
                {t("Could not submit your application due to validation errors. Please go back and fix these any try again.")}
              </div>}
              {allErrors.length === 0 && <button
                className="btn btn-primary submit-application mx-auto"
                onClick={this.props.submit}
                disabled={this.props.isSubmitting}
              >
                {t("Submit")}
              </button>}
            </div>

          </div>
        </div>

        {this.props.sectionModels && 
          this.props.sectionModels.filter(sm => sm.questionModels.length > 0).map(sm => {
            return <div key={"section_" + sm.section.id}>
              <h2>{sm.section.name}</h2>
              {sm.questionModels &&
                sm.questionModels.filter(qm => this.dependentQuestionFilter(qm.question, allAnswers)).map(qm => {
                  return (
                    qm.question && (
                      <div className={"confirmation answer"}>
                        <div class="row">
                          <div class="col">
                            <h5>{qm.question.headline}</h5>
                          </div>
                        </div>
                        <div class="row">
                          <div class="col">
                            <p class="answer-value">
                              <AnswerValue answer={qm.answer} question={qm.question} />
                              {qm.validationError && <div className="alert alert-danger alert-container">{qm.validationError}</div>}
                            </p>
                          </div>
                        </div>
                      </div>
                    )
                  );
                })}
            </div>
          })}
        
        {allErrors.length > 0 && <div class="alert alert-danger alert-container">
          {t("Could not submit your application due to validation errors. Please go back and fix these any try again.")}
        </div>}
        {allErrors.length === 0 && <button
          className="btn btn-primary submit-application mx-auto"
          onClick={this.props.submit}
          disabled={this.props.isSubmitting}
        >
          {t("Submit")}
        </button>}
      </div>
    );
  }
}


const Confirmation = withTranslation()(ConfirmationComponent);


class SubmittedComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      withdrawModalVisible: false,
      isError: false,
      errorMessage: "",
      submitValidationErrors: [],
    };
  }

  handleWithdrawOK = event => {
    applicationFormService.withdraw(this.props.responseId).then(resp => {
      this.setState(
        {
          isError: resp.isError,
          errorMessage: resp.message,
          withdrawModalVisible: false
        },
        () => {
          if (this.props.onWithdrawn) {
            this.props.onWithdrawn();
          }
        }
      );
    });
  };

  handleEditOK = event => {
    if (this.props.onEdit) {
      this.props.onEdit();
    }
  };

  handleWithdrawCancel = event => {
    this.setState({
      withdrawModalVisible: false
    });
  };

  handleWithdraw = event => {
    this.setState({
      withdrawModalVisible: true
    });
  };

  handleEdit = event => {
    this.setState({
      editAppModalVisible: true
    });
  };

  cancelEditModal = event => {
    this.setState({
      editAppModalVisible: false
    });
  };

  viewsubmission = ()=> {
    window.location.href = `/${this.props.event.key}/apply/view`;
 }

  render() {
    const t = this.props.t;
    const initialText = this.props.event && this.props.event.event_type === "CALL" 
      ? t("Thank you for responding to the")
      : this.props.event.event_type === "JOURNAL"
      ? t("Thank you for submitting an article to the") 
      : t("Thank you for applying for"); 

    return (
      <div class="submitted">
        <h2>{t("Thank you for applying!")}</h2>
        {this.state.isError && (
          <div className={"alert alert-danger alert-container"}>
            {this.state.errorMessage}
          </div>
        )}

        <p class="thank-you">
          {initialText + " "} {this.props.event ? this.props.event.name : ""}. {" "}
          {this.props.event.event_type === "JOURNAL" 
          ? t("Your article will be reviewed by our appointed reviewers and we will get back to you as soon as possible.")
          : t("Your application will be reviewed by our committee and we will get back to you as soon as possible.")}
        </p>

        <p class="timestamp">
          {this.props.event.event_type === "JOURNAL" 
          ? t("You submitted your article on") + " "
          : t("You submitted your application on") + " "}
          {this.props.timestamp && this.props.timestamp.toLocaleString()}
        </p>

        <div class="submitted-footer">
          <button class="btn btn-danger" onClick={this.handleWithdraw}>
            {this.props.event.event_type === "JOURNAL" 
            ? t("Withdraw Article Submission") 
            : t("Withdraw Application")}
          </button>
        </div>
        
        {this.props.event.event_type === "JOURNAL" 
        ? <div class="submitted-footer">
            <button class="btn btn-secondary" onClick={this.viewsubmission}>
              {t("View Submission(s)")}
            </button>
          </div>
        : <div class="submitted-footer">
            <button class="btn btn-primary" onClick={this.handleEdit}>
              {t("Edit Application")}
            </button>
          </div>}

        <ConfirmModal
          visible={this.state.withdrawModalVisible}
          onOK={this.handleWithdrawOK}
          onCancel={this.handleWithdrawCancel}
          okText={t("Yes - Withdraw")}
          cancelText={t("No - Don't withdraw")}>

          <p>
            {t("By continuing, your submitted application will go into draft state. You MUST press Submit again after you make your changes for your application to be considered in the selection.")}
          </p>
        </ConfirmModal>

        <ConfirmModal
          visible={this.state.editAppModalVisible}
          onOK={this.handleEditOK}
          onCancel={this.cancelEditModal}
          okText={t("Yes - Edit application")}
          cancelText={t("No - Don't edit")}>
          <p>
            {t("Do you want to edit your application to") + " "} {this.props.event ? this.props.event.name : ""}?
          </p>
        </ConfirmModal>
      </div>
    );
  }
}

const Submitted = withTranslation()(SubmittedComponent);


class ApplicationFormInstanceComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      isSubmitting: false,
      isError: false,
      isSubmitted: props.response && props.response.is_submitted,
      isEditing: false,
      responseId: props.response && props.response.id,
      submittedTimestamp: props.response && props.response.submitted_timestamp,
      errorMessage: "",
      errors: [],
      answers: props.response ? props.response.answers : [],
      unsavedChanges: false,
      startStep: 0,
      new_response: !props.response,
      outcome: props.response && props.response.outcome,
      submitValidationErrors: [],
      parent_id: props.match.params.id || null,
      allow_multiple_submission:props.event.event_type === "JOURNAL" ? true : false
    };
  }

  handleSubmit = event => {
    event.preventDefault();
    this.setState(
      {
        isSubmitting: true
      },
      () => {
        const promise = this.state.new_response 
          ? applicationFormService.submit(this.props.formSpec.id, true, this.state.answers)
          : applicationFormService.updateResponse(this.state.responseId, this.props.formSpec.id, true, this.state.answers);
        
        promise.then(resp => {
            const submitError = resp.response_id === null && resp.status !== 422;
            this.setState(prevState => ({
              submitValidationErrors: resp.status === 422 && resp.errors,
              isError: submitError,
              errorMessage: resp.message,
              isSubmitting: false,
              isSubmitted: resp.response_id !== null && resp.status !== 422 && resp.is_submitted,
              isEditing: false,
              submittedTimestamp: resp.submitted_timestamp,
              unsavedChanges: false,
              new_response: false,
              responseId: prevState.responseId || resp.response_id
            }));
          });
      }
    );
  };

  handleSave = answers => {
    this.setState(
      prevState => {
        return {
          isSaving: true,
          answers: prevState.answers
            .filter(a => !answers.includes(a.question_id))
            .concat(answers)
        };
      },
      () => {
        if (this.state.new_response) {
          applicationFormService
            .submit(this.props.formSpec.id, false, this.state.answers, this.state.parent_id, this.state.allow_multiple_submission)
            .then(resp => {
              let submitError = resp.response_id === null;
              this.setState({
                isError: submitError,
                errorMessage: resp.message,
                isSubmitted: resp.is_submitted,
                submittedTimestamp: resp.submitted_timestamp,
                new_response: false,
                unsavedChanges: false,
                isSaving: false,
                responseId: resp.response_id
              });
            });
        } else {
          applicationFormService
            .updateResponse(
              this.state.responseId,
              this.props.formSpec.id,
              false,
              this.state.answers
            )
            .then(resp => {
              let saveError = resp.response_id === null;
              this.setState({
                isError: saveError,
                errorMessage: resp.message,
                isSubmitted: resp.is_submitted,
                submittedTimestamp: resp.submitted_timestamp,
                unsavedChanges: false,
                isSaving: false
              });
            });
        }
      }
    );
  };

  handleWithdrawn = () => {
    this.props.history.push("/");
  };

  handleAnswerChanged = (answers, save) => {
    if (answers) {
      this.setState(prevState => {
        return {
          answers: prevState.answers
            .filter(a => !answers.map(a => a.question_id).includes(a.question_id))
            .concat(answers),
          submitValidationErrors: prevState.submitValidationErrors.filter(e => !answers.map(a => a.question_id).includes(e.question_id))
        };
      }, () => {
        if (save) {
          this.handleSave([]);
        }
      });
    }
  };

  handleStepChange = () => {
    window.scrollTo(0, 0);
  };

  getSubmitValidationError = (q) => {
    const validationError = this.state.submitValidationErrors.find(e => e.question_id === q.id);
    if (!validationError) {
      return "";
    }

    if (validationError.error === "required") {
      return this.props.t("An answer is required.");
    }

    if (validationError.error === "validation_regex_failed") {
      return q.validation_text;
    }

    if (validationError.error === "invalid_option") {
      return this.props.t("Invalid option selected.");
    }

    return "";
  }

  render() {
    const {
      isError,
      isSubmitted,
      isEditing,
      errorMessage,
      answers,
      isSubmitting,
      outcome
    } = this.state;

    if (isError) {
      return <div className={"alert alert-danger alert-container"}>
        {errorMessage}
      </div>;
    }

    if (outcome === "ACCEPTED" || outcome === "REJECTED") {
      return <div className={"alert alert-success alert-container"}>
        {outcome === "ACCEPTED" && <div>
          <p>{this.props.t("You have already been accepted to this event.")}</p>
          <Link to={`/${this.props.event.key}/offer`} className="btn btn-primary">
            {this.props.t("View Offer")}
          </Link>
        </div>}
        {outcome === "REJECTED" && <p>{this.props.t("Unfortunately your application to this event has been rejected, you are not able to apply again.")}</p>}
      </div>;
    }

    if (isSubmitted && !isEditing) {
      return (
        <Submitted
          timestamp={this.state.submittedTimestamp}
          onWithdrawn={this.handleWithdrawn}
          responseId={this.state.responseId}
          event={this.props.event}
          onEdit={() => this.setState({ isEditing: true, startStep: 0 })} // StartStep to jump to step 1 in the Stepzilla
        />
      );
    }

    const includeEntityDueToDependentQuestion = (entity) => {
      if (isEntityDependentOnAnswer(entity)) {
        const answer = findDependentQuestionAnswer(entity, this.state.answers);
        return answer ? doesAnswerMatch(entity, answer) : false;
      } else {
        return true;
      }
    }

    const sections =
      this.props.formSpec.sections &&
      this.props.formSpec.sections.slice()
        .filter(includeEntityDueToDependentQuestion)
        .sort((a, b) => a.order - b.order);
    const sectionModels =
      sections &&
      sections.map(section => {
        return {
          section: section,
          questionModels: section.questions.map(q => {
            return {
              question: q,
              answer: answers.find(a => a.question_id === q.id),
              validationError: this.getSubmitValidationError(q)
            };
          })
        };
      });

    const steps =
      sectionModels &&
      sectionModels.map((model, i) => {
        return {
          name: this.props.t("Step") + " " + i,
          component: (
            <Section
              key={"section_" + model.section.id}
              showQuestionBasedOnSavedFormAnswers={includeEntityDueToDependentQuestion}
              section={model.section}
              questionModels={model.questionModels}
              answerChanged={this.handleAnswerChanged}
              save={this.handleSave}
              changed={() => this.setState({ unsavedChanges: true })}
              unsavedChanges={this.state.unsavedChanges}
              isSaving={this.state.isSaving}
              responseId={this.state.responseId}
              stepProgress={i}
              t={this.props.t}
            />
          )
        };
      });

    steps.push({
      name: this.props.t("Confirmation"),
      component: (
        <Confirmation
          sectionModels={sectionModels}
          submit={this.handleSubmit}
          isSubmitting={isSubmitting}
        />
      )
    });

    return (
      <div class="application-form-container">
        <div className="step-progress">
          <StepZilla
            steps={steps}
            onStepChange={this.handleStepChange}
            backButtonCls={"btn btn-prev btn-secondary"}
            nextButtonCls={"btn btn-next btn-primary float-right"}
            startAtStep={this.state.startStep}
            nextButtonText={this.props.t("Next")}
            backButtonText={this.props.t("Previous")}
          />

          <ReactToolTip />
        </div>
        {isSubmitting && <h2 class="submitting">{this.props.t("Saving Responses")}...</h2>}
      </div>
    );
  }
}

const ApplicationFormInstance = withRouter(withTranslation()(ApplicationFormInstanceComponent));

class ApplicationListComponent extends Component {
  constructor(props) {
    super(props);
    this.state = {
    }
  }

  getCandidate = (allQuestions, response) => {
    const nominating_capacity = answerByQuestionKey("nominating_capacity", allQuestions, response.answers);
    if (nominating_capacity === "other") {
      let firstname = answerByQuestionKey("nomination_firstname", allQuestions, response.answers);
      let lastname = answerByQuestionKey("nomination_lastname", allQuestions, response.answers);
      return firstname + " " + lastname;
    }
    return  this.props.event.event_type ==='JOURNAL' ? this.props.t("Submission") + " " + response.id : this.props.t("Self Nomination");
  }

  getStatus = (response) => {
    if (response.is_submitted) {
      return <span>{this.props.t("Submitted")}</span>
    }
    else {
      return <span>{this.props.t("In Progress")}</span>
    }
  }

  getAction = (response) => {
    if (response.is_submitted) {
      return (
        <button
          className="btn btn-warning btn-sm custom-button"
          onClick={() =>
            (window.location.href = `/${this.props.event.key}/responseDetails/${response.id}`)
          }
        >
          {this.props.t("View")}
        </button>
      );
    } else {
      return (
        <button
          className="btn btn-success btn-sm custom-button"
          onClick={() =>
            (window.location.href = `/${this.props.event.key}/apply/continue/${response.id}`)
          }
        >
          {this.props.t("Continue")}
        </button>
      );
    }
  }

  formatDate = (dateString) => {
    return moment(dateString).format("D MMM YYYY, H:mm:ss [(UTC)]");
  };

  getSubmission = (response) => {
       return response.answers[0].value
  };

  renderSections() {
    const applicationForm = this.state.applicationForm;
    const applicationData = this.state.applicationData;
    let html = [];

    if (applicationForm && applicationData) {
      applicationForm.sections.forEach((section) => {
        html.push(
          <div key={section.name} className="section">
            <div className="flex baseline">
              <h3>{section.name}</h3>
            </div>
            <div className="Q-A">{this.renderResponses(section)}</div>
          </div>
        );
      });
    }
    return html;
  }

  renderResponses(section) {
    const applicationData = this.state.applicationData;
    const questions = section.questions.map((q) => {
      const a = applicationData.answers.find((a) => a.question_id === q.id);
      if (q.type === "information") {
        return <h4>{q.headline}</h4>;
      }
      return (
        <div key={q.id} className="question-answer-block">
          <p>
            <span className="question-headline">{q.headline}</span>
            {q.description && (
              <span className="question-description">
                <br />
                {q.description}
              </span>
            )}
          </p>
          <h6>
            <AnswerValue answer={a} question={q} />
          </h6>
        </div>
      );
    });
    return questions;
  }

  getOutcome = (response) => {
    if (response.outcome) {
      const badgeClass =
        response.outcome === "ACCEPTED"
          ? "badge-success"
          : response.outcome === "REJECTED"
          ? "badge-danger "
          : "badge-warning ";
        const outcome= response.outcome==='ACCEPTED'?this.props.t("ACCEPTED"):response.outcome==='REJECTED'?
        this.props.t("REJECTED"):response.outcome==='ACCEPT_W_REVISION'?
        this.props.t("ACCEPTED WITH REVISION"):response.outcome==='REJECT_W_ENCOURAGEMENT'?
        this.props.t("REJECTED WITH ENCOURAGEMENT TO RESUMIT"):this.props.t("REVIEWING");
      return (
        <span class={`badge badge-pill ${badgeClass}`}>{outcome}</span>
      );
    }
    return (
      <span class="badge badge-pill badge-secondary">
        {this.props.t("PENDING")}
      </span>
    );
  };

  newSubmission = (id) => {
    window.location.href = `/${this.props.event.key}/apply/new/${id}`;
  };

  getLastResponse = (response) => {
    if (response.children.length === 0) return response;
    return this.getLastResponse(response.children[response.children.length - 1]);
  };

  buildResponseChains = (responses) => {
    const responseMap = responses.reduce((map, response) => {
      map[response.id] = { ...response, children: [] };
      return map;
    }, {});
    
    const chains = [];
    
    responses.forEach((response) => {
      if (response.parent_id !== null && responseMap[response.parent_id]) {
        responseMap[response.parent_id].children.push(responseMap[response.id]);
      } else {
        chains.push(responseMap[response.id]);
      }
    });
    
    return chains.sort((a, b) => this.getLastResponse(b).id - this.getLastResponse(a).id);
  };

  toggleChain = (chainId) => {
    this.setState((prevState) => {
      const expandedChains = prevState.expandedChains ? { ...prevState.expandedChains } : {};
      expandedChains[chainId] = !expandedChains[chainId];
      return { expandedChains };
    });
  };

  renderResubmitButton = (chain) => {
    const lastResponse = this.getLastResponse(chain);

    if (lastResponse && lastResponse.outcome && lastResponse.outcome !== 'ACCEPTED') {
      return (
        <div className="resubmit-bar">
          <button 
            onClick={() => this.newSubmission(lastResponse.id)} 
            className="btn btn-primary resubmit-button"
          >
            {this.props.t("Resubmit an article")}
          </button>
        </div>
      );
    }
  
    return null;
  };
  
  
  renderEntireChain = (response) => {
    const children = response.children.slice().reverse();
    return (
      <Fragment key={response.id}>
        {children.map((childResponse) => this.renderEntireChain(childResponse))}
        <tr key={response.id} className="response-row">
          <td><strong>{this.getSubmission(response)}</strong></td>
          <td>{this.getStatus(response)}</td>
          <td>{this.getOutcome(response)}</td>
          <td>{this.getAction(response)}</td>
        </tr>
      </Fragment>
    );
  };

  renderResponseChain = (chain) => {
    
    return (
      <Fragment key={chain.id}>
        <tr onClick={() => this.toggleChain(chain.id)} className="chain-header">
          <td colSpan="5" className="chain-header-title" >
            <span className="chain-toggle-icon">
              {this.state.expandedChains && this.state.expandedChains[chain.id] ? (
                <div className="resubmit-container">
                  {this.renderResubmitButton(chain)}
                  <i className="fas fa-chevron-up" />
                </div>
              ) 
              : (
                <div className="resubmit-container">
                  {this.renderResubmitButton(chain)}
                  <i className="fas fa-chevron-down" />
                </div>
              )
              }

            </span>
            <strong>{chain.answers[0].value}</strong>
          </td>
        </tr>
        {this.state.expandedChains && this.state.expandedChains[chain.id] && 
          this.renderEntireChain(chain)
        }
      </Fragment>
    );

  };


  render() {
    let allQuestions = _.flatMap(this.props.formSpec.sections, s => s.questions);
    const title = this.props.event.event_type ==='JOURNAL' ? this.props.t("Your Submissions") : this.props.t("Your Nominations");
    let firstColumn = this.props.event.event_type ==='JOURNAL' ? this.props.t("Submission") : this.props.t("Nominee");

    if (this.props.event.event_type =='JOURNAL') {
      const responseChains = this.buildResponseChains(this.props.responses);
      return ( 
        <div className="response-chains-container">
        <h4 className="response-chains-title">{title}</h4>
        <table className="table response-chains-table">
          <thead>
            <tr>
              <th scope="col" colSpan="5" className="response-chains-header">{firstColumn}</th>
            </tr>
          </thead>
          <tbody>
            {responseChains.map((chain, index) => this.renderResponseChain(chain, index))}
          </tbody>
        </table>
      </div>
      );
    }
    return <div>
    <h4>{title}</h4>
    <table class="table">
      <thead>
        <tr>
          <th scope="col">{firstColumn}</th>
          <th scope="col">{this.props.t("Status")}</th>
          <th scope="col"></th>
        </tr>
      </thead>
      <tbody>
        {this.props.responses.map(response => {
          return <tr key={"response_" + response.id}>
            <td>{this.getCandidate(allQuestions, response)}</td>
            <td>{this.getStatus(response)}</td>
            <td>{this.getAction(response)}</td>
          </tr>
        })}
      </tbody>
    </table>
  </div>;
  }
}


const ApplicationList = withRouter(withTranslation()(ApplicationListComponent));


class ApplicationForm extends Component {
  constructor(props) {
    super(props);
    this.state = {
      isLoading: true,
      isError: false,
      errorMessage: "",
      formSpec: null,
      responses: [],
      selectedResponse: null,
      journalSubmissionFlag: false,
      listselectedResponse: null,
      continue: false,
      view: false,
      chain: false,
    }
  }

  componentDidMount() {
    const eventId = this.props.event ? this.props.event.id : 0;
    Promise.all([
      applicationFormService.getForEvent(eventId),
      applicationFormService.getResponse(eventId),
      eventService.getEvent(eventId)
    ]).then(responses => {
      const [formResponse, responseResponse, eventResponse] = responses;
      const selectFirstResponse = formResponse && formResponse.formSpec && !formResponse.formSpec.nominations && responseResponse.response.length > 0;
      this.setState({
        formSpec: formResponse.formSpec,
        responses: responseResponse.response,
        isError: formResponse.formSpec === null || responseResponse.error,
        errorMessage: (formResponse.error + " " + responseResponse.error).trim(),
        isLoading: false,
        selectedResponse: selectFirstResponse ? responseResponse.response[0] : null,
        responseSelected: selectFirstResponse,
        event: eventResponse.event
      });
    });
    
  }

  responseSelected = response => {
    this.setState({
      selectedResponse: response,
      responseSelected: true
    });
  }

  newNomination = () => {
    this.setState({
      responseSelected: true
    });
  }

  newSubmission = () => {
    window.location.href = `/${this.props.event.key}/apply/new`;
  };

  render() {
    const {
      isLoading,
      isError,
      errorMessage,
      formSpec,
      responses,
      selectedResponse,
      responseSelected,
      listselectedResponse,} = this.state;

    if (isLoading) {
      return (<Loading />);
    }

    if (isError) {
      return <div className={"alert alert-danger alert-container"}>{errorMessage}</div>;
    }
    
    if (this.props.event.event_type === "JOURNAL") {
      if (this.props.journalSubmissionFlag) {
        return (
          <ApplicationFormInstance
            formSpec={formSpec}
            response={selectedResponse.is_submitted ? null : selectedResponse}
            event={this.props.event}
          />
        );
      }
      if (this.props.view) {
        
        return (
          <div>
            {/* <br /> */}
            <hr/>
            <button
              className="btn btn-primary"
              onClick={() => this.newSubmission()}
              >
              {this.props.t("Start a new submission")} &gt;
            </button>
              <hr/>
            <ApplicationList
              responses={responses}
              event={this.state.event}
              formSpec={formSpec}
              click={this.responseSelected}
            />
            
          </div>
        );
      }
      if (this.props.chain) {
        const isIdAndNotParent=(listResponse, id) =>{
          const isIdPresent = listResponse.some(entry => entry.id === id);
          const isNotAParent = !listResponse.some(entry => entry.parent_id === id);
          return isIdPresent && isNotAParent;
      }
          if (!isIdAndNotParent(responses, parseInt(this.props.match.params.id))) {
            return <Redirect to={`/${this.props.event.key}/apply/view`} />
          }
        return (
          <ApplicationFormInstance
            formSpec={formSpec}
            response={null}
            event={this.props.event}
          />
        );
      }
      if (this.props.continue) {
        const response = listselectedResponse.find(
          (item) => item.id === parseInt(this.props.match.params.id));
          if (response == null || response.outcome != null) {
            return <Redirect to={`/${this.props.event.key}/apply/view`} />
          }
        return (
          <ApplicationFormInstance
            formSpec={formSpec}
            response={response}
            event={this.props.event}
          />
        );
      }
      return (
        <ApplicationFormInstance
          formSpec={formSpec}
          response={null}
          event={this.props.event}
        />
      );
    } else if (
      formSpec.nominations &&
      responses.length > 0 &&
      !responseSelected
    ) {
      let newForm =
        this.state.event.event_type === "JOURNAL"
          ? this.props.t("New Submission") + " "
          : this.props.t("New Nomination") + " ";
      return (
        <div>
          <ApplicationList
            responses={responses}
            event={this.state.event}
            formSpec={formSpec}
            click={this.responseSelected}
          />
          <br />

          <button
            className="btn btn-primary"
            onClick={() => this.newNomination()}
          >
            {newForm} &gt;
          </button>
        </div>
      );
    } else {
      return (
        <ApplicationFormInstance
          formSpec={formSpec}
          response={selectedResponse}
          event={this.props.event}
        />
      );
    }
  }
}
export default withRouter(withTranslation()(ApplicationForm));
