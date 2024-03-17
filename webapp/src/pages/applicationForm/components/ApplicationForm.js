import React, { Component } from "react";
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
import _ from "lodash";
import { withTranslation } from 'react-i18next';
import AnswerValue from '../../../components/answerValue'
import FormSelectOther from "../../../components/form/FormSelectOther";
import FormMultiCheckboxOther from "../../../components/form/FormMultiCheckboxOther";
import FormCheckbox from "../../../components/form/FormCheckbox";
import { eventService } from "../../../services/events";

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
      hasValidated: false,
      validationStale: false
    };
  }

  onChange = (question, value) => {
    const newAnswer = {
      question_id: question.id,
      value: value
    };
    if (this.props.answerChanged) {
      this.props.answerChanged(newAnswer);
    }
  }

  isValidated = () => {
    if (this.props.triggerValidation) {
      const isValid = this.props.triggerValidation(this.props.model);
      return isValid;
    }
    return true;
  }

  render() {
    const {
      hasValidated,
      validationStale
    } = this.state;

    const model = this.props.model;

    return (
      <div className={"section"}>
        <div className={"headline"}>
          <h1>{model.section.name}</h1>
          <div className="description">
            <MarkdownRenderer children={model.section.description}/>
          </div>
        </div>
        {model.questionModels &&
          model.questionModels
            .filter(q => q.isVisible)
            .map(qm => (
              <FieldEditor
                key={"question_" + qm.question.id}
                question={qm.question}
                answer={qm.answer}
                validationError={qm.validationError}
                onChange={this.onChange}
                responseId={this.props.responseId}
              />
            )
            )
        }
        {this.props.unsavedChanges && !this.props.isSaving && (
          <button className="btn btn-secondary" onClick={this.props.save} >
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

  render() {
    const t = this.props.t;
    const initialText = this.props.event && this.props.event.event_type === "CALL" 
      ? t("Thank you for responding to the")
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
          {t("Your application will be reviewed by our committee and we will get back to you as soon as possible.")}
        </p>

        <p class="timestamp">
          {t("You submitted your application on") + " "}
          {this.props.timestamp && this.props.timestamp.toLocaleString()}
        </p>

        <div class="submitted-footer">
          <button class="btn btn-danger" onClick={this.handleWithdraw}>
            {t("Withdraw Application")}
          </button>
        </div>

        <div class="submitted-footer">
          <button class="btn btn-primary" onClick={this.handleEdit}>
            {t("Edit Application")}
          </button>
        </div>

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

    let sectionModels = this.props.formSpec.sections &&
      this.props.formSpec.sections.map(section => ({
        section: section,
        isVisible: false,
        hasValidated: false,
        questionModels: section.questions.map(q => {
          return {
            question: q,
            answer: props.response && props.response.answers.find(a => a.question_id === q.id),
            isVisible: false,
          };
        }).sort((a, b) => a.question.order - b.question.order)
      })).sort((a, b) => a.section.order - b.section.order);

    sectionModels.forEach(sectionModel => {
      sectionModel.isVisible = this.isEntityVisible(sectionModel.section, sectionModels);
      sectionModel.questionModels.forEach(qm => {
        qm.isVisible = this.isEntityVisible(qm.question, sectionModels);
      });
    });

    this.state = {
      isSubmitting: false,
      isError: false,
      isSubmitted: props.response && props.response.is_submitted,
      isEditing: false,
      responseId: props.response && props.response.id,
      submittedTimestamp: props.response && props.response.submitted_timestamp,
      errorMessage: "",
      errors: [],
      unsavedChanges: false,
      startStep: 0,
      new_response: !props.response,
      outcome: props.response && props.response.outcome,
      sections: sectionModels
    };

  }

  validate = (questionModel) => {
    let errors = [];
    
    const question = questionModel.question;
    const answer = questionModel.answer;

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

  triggerValidation = (sectionModel) => {
    const newSectionModel = {
      ...sectionModel,
      hasValidated: true,
      questionModels: sectionModel.questionModels.map(qm => ({
          ...qm,
          validationError: this.validate(qm)
        }))
    };
    
    const isValid = newSectionModel.questionModels.filter(qm => qm.isVisible).every(qm => !qm.validationError);

    this.setState(prevState => ({
      sections: prevState.sections.map(s => s.section.id === sectionModel.section.id ? newSectionModel : s)
    }));

    return isValid;
  }

  isEntityVisible = (entity, sectionModels, newAnswer) => {
    if (isEntityDependentOnAnswer(entity)) {
      const dependentQuestionModel = sectionModels.filter(s=>s.isVisible).flatMap(s => s.questionModels).find(qm => qm.question.id === entity.depends_on_question_id);
      if (!dependentQuestionModel) {
        return false;
      }
      const answer = newAnswer && newAnswer.question_id === dependentQuestionModel.question.id ? newAnswer : dependentQuestionModel.answer;
      return dependentQuestionModel.isVisible && doesAnswerMatch(entity, answer);
    }
    return true;
  }

  handleSubmit = event => {
    event.preventDefault();
    this.setState(
      {
        isSubmitting: true
      },
      () => {
        const answers = this.state.sections.flatMap(s => s.questionModels).map(qm => qm.answer);
        const promise = this.state.new_response 
          ? applicationFormService.submit(this.props.formSpec.id, true, answers)
          : applicationFormService.updateResponse(this.state.responseId, this.props.formSpec.id, true, answers);
        
        promise.then(resp => {
            const submitError = resp.response_id === null && resp.status !== 422;
            this.setState(prevState => ({
              isError: submitError,
              errorMessage: resp.message,
              isSubmitting: false,
              isSubmitted: resp.response_id !== null && resp.status !== 422 && resp.is_submitted,
              isEditing: false,
              submittedTimestamp: resp.submitted_timestamp,
              unsavedChanges: false,
              new_response: false,
              responseId: prevState.responseId || resp.response_id,
              sections: prevState.sections.map(s => ({
                ...s,
                hasValidated: true,
                questionModels: s.questionModels.map(qm => ({
                  ...qm,
                  validationError: resp.status === 422 && this.getSubmitValidationError(qm.question, resp.errors)
                }))
              }))
            }));
          });
      }
    );
  };

  handleSave = () => {
    this.setState(
      {
        isSaving: true
      },
      () => {
        const answers = this.state.sections.flatMap(s => s.questionModels).map(qm => qm.answer);
        if (this.state.new_response) {
          applicationFormService
            .submit(this.props.formSpec.id, false, answers)
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
              answers
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

  handleAnswerChanged = (answer) => {
    this.setState(prevState => ({
      sections: prevState.sections.map(s => ({
        ...s,
        isVisible: this.isEntityVisible(s.section, prevState.sections, answer),
        questionModels: s.questionModels.map(qm => ({
          ...qm,
          answer: qm.question.id === answer.question_id ? answer : qm.answer,
          isVisible: this.isEntityVisible(qm.question, prevState.sections, answer),
          validationError: s.hasValidated ? this.validate(qm) : ""
        }))
      })),
      unsavedChanges: true
    }));
  }

  handleStepChange = () => {
    window.scrollTo(0, 0);
  };

  getSubmitValidationError = (q, submitValidationErrors) => {
    const validationError = submitValidationErrors.find(e => e.question_id === q.id);
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
      isSubmitting,
      outcome,
      sections
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
        {outcome === "REJECTED" && <p>{this.props.t("Unfortunately your application to this event was not successful, you are not able to apply again.")}</p>}
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

    const steps =
      sections &&
      sections.filter(s=>s.isVisible).map((model, i) => {
        return {
          name: this.props.t("Step") + " " + i,
          component: (
            <Section
              key={"section_" + model.section.id}
              model={model}
              answerChanged={this.handleAnswerChanged}
              save={this.handleSave}
              unsavedChanges={this.state.unsavedChanges}
              isSaving={this.state.isSaving}
              responseId={this.state.responseId}
              stepProgress={i}
              t={this.props.t}
              triggerValidation={this.triggerValidation}
            />
          )
        };
      });

    steps.push({
      name: this.props.t("Confirmation"),
      component: (
        <Confirmation
          sectionModels={sections}
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
    return  (this.props.event.event_type ==='JOURNAL' || this.props.event.event_type ==='CONTINUOUS_JOURNAL') ? this.props.t("Submission") + " " + response.id : this.props.t("Self Nomination");
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
      return <button className="btn btn-warning btn-sm" onClick={() => this.props.click(response)}>{this.props.t("View")}</button>
    }
    else {
      return <button className="btn btn-success btn-sm" onClick={() => this.props.click(response)}>{this.props.t("Continue")}</button>
    }
  }

  render() {
    let allQuestions = _.flatMap(this.props.formSpec.sections, s => s.questions);
    const title = (this.props.event.event_type ==='JOURNAL' || this.props.event.event_type ==='CONTINUOUS_JOURNAL') ? this.props.t("Your Submissions") : this.props.t("Your Nominations");
    let firstColumn = (this.props.event.event_type ==='JOURNAL' || this.props.event.event_type ==='CONTINUOUS_JOURNAL') ? this.props.t("Submission") : this.props.t("Nominee");
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
    </div>
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
      selectedResponse: null
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
      const selectFirstResponse = !formResponse.formSpec.nominations && responseResponse.response.length > 0;
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

  render() {
    const {
      isLoading,
      isError,
      errorMessage,
      formSpec,
      responses,
      selectedResponse,
      responseSelected } = this.state;

    if (isLoading) {
      return (<Loading />);
    }

    if (isError) {
      return <div className={"alert alert-danger alert-container"}>{errorMessage}</div>;
    }

    if (formSpec.nominations && responses.length > 0 && !responseSelected) {
      let newForm = (this.state.event.event_type ==='JOURNAL' || this.state.event.event_type ==='CONTINUOUS_JOURNAL') ? this.props.t("New Submission") + " " : this.props.t("New Nomination") + " ";
      return <div>
        <ApplicationList responses={responses} event={this.state.event} formSpec={formSpec} click={this.responseSelected} /><br />
        <button className="btn btn-primary" onClick={() => this.newNomination()}>{newForm} &gt;</button>
      </div>
    }
    else {
      return <ApplicationFormInstance
        formSpec={formSpec}
        response={selectedResponse}
        event={this.props.event} />
    }
  }

}


export default withRouter(withTranslation()(ApplicationForm));

