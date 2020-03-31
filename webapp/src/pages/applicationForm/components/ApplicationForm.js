import React, { Component } from "react";
import { withRouter } from "react-router";
import { applicationFormService } from "../../../services/applicationForm";

import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import FormTextArea from "../../../components/form/FormTextArea";
import FormDate from "../../../components/form/FormDate";
import ReactToolTip from "react-tooltip";
import { ConfirmModal } from "react-bootstrap4-modal";
import StepZilla from "react-stepzilla";
import FormFileUpload from "../../../components/form/FormFileUpload";
import { fileService } from "../../../services/file/file.service";
import FormMultiCheckbox from "../../../components/form/FormMultiCheckbox";
import FormReferenceRequest from "./ReferenceRequest";

const baseUrl = process.env.REACT_APP_API_URL;

const SHORT_TEXT = "short-text";
const SINGLE_CHOICE = "single-choice";
const LONG_TEXT = ["long-text", "long_text"];
const MULTI_CHOICE = "multi-choice";
const MULTI_CHECKBOX = "multi-checkbox";
const FILE = "file";
const DATE = "date";
const REFERENCE_REQUEST = "reference";

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
  return entityToCheck.show_for_values.map(_ => _.value).indexOf(answer.value) > -1;
}

class FieldEditor extends React.Component {
  constructor(props) {
    super(props);
    this.id = "question_" + props.question.id;
    this.state = {
      uploading: false,
      uploadPercentComplete: 0,
      uploadError: "",
      uploaded: false
    }
  }

  handleChange = event => {
    // Some components (datepicker, custom controls) return pass the value directly rather than via event.target.value
    const value = event && event.target ? event.target.value : event;

    if (this.props.onChange) {
      this.props.onChange(this.props.question, value);
    }
  };

  handleChangeDropdown = (name, dropdown) => {
    if (this.props.onChange) {
      this.props.onChange(this.props.question, dropdown.value);
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

  formControl = (key, question, answer, validationError, responseId) => {
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
      case DATE:
        return (
          <FormDate
            Id={this.id}
            name={this.id}
            label={question.description}
            value={answer ? answer.value : answer}
            placeholder={question.placeholder}
            onChange={this.handleChange}
            key={"i_" + key}
            showError={validationError}
            errorText={validationError}
            required={question.is_required} />
        );
      case REFERENCE_REQUEST:
        return (
          <FormReferenceRequest
            Id={this.id}
            name={this.id}
            label={question.description}
            value={answer ? answer.value : answer}
            placeholder={question.placeholder}
            onChange={this.handleChange}
            key={"i_" + key}
            showError={validationError}
            errorText={validationError}
            required={question.is_required} 
            options={question.options}
            responseId={responseId}/>
        )
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
        <h4>{this.props.question.headline}</h4>
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
      validationStale: false
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

  validate = (questionModel, updatedAnswer) => {
    let errors = [];
    const question = questionModel.question;
    const answer = updatedAnswer || questionModel.answer;

    if (question.is_required && (!answer || !answer.value)) {
      errors.push("An answer is required.");
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
          <h2>{section.name}</h2>
          <p>{section.description}</p>
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
            Save for later...
          </button>
        )}
        {this.props.isSaving && <span class="saving mx-auto">Saving...</span>}
        {hasValidated && !validationStale && (
          <div class="alert alert-danger alert-container">
            Please fix the errors before continuing.
          </div>
        )}
      </div>
    );
  }
}

function AnswerValue(props) {
  if (props.qm.answer && props.qm.answer.value) {
    switch (props.qm.question.type) {
      case MULTI_CHOICE:
        const options = props.qm.question.options.filter(o => o.value === props.qm.answer.value);
        if (options) {
          return options[0].label;
        }
        else {
          return props.qm.answer.value;
        }
      case FILE:
        return <a href={baseUrl + "/api/v1/file?filename=" + props.qm.answer.value}>Uploaded File</a>
      default:
        return props.qm.answer.value;
    }
  }
  return "No answer provided.";
}

class Confirmation extends React.Component {

  render() {
    return (
      <div>
        <div class="row">
          <div class="col confirmation-heading">
            <h2>Review your Answers</h2>
            <p>
              Please confirm that your answers are correct. Use the previous
              button to correct them if they are not. You can also exit and come back
              later as they have all been saved.

              Click the SUBMIT button once you are happy to submit your answers to the committee.
            </p>

            <div class="alert alert-warning">
              <span class="fa fa-exclamation-triangle"></span> You MUST click SUBMIT before the deadline for your application to be considered!
            </div>

            <div class="text-center">
              <button
                className="btn btn-primary submit-application mx-auto"
                onClick={this.props.submit}
                disabled={this.props.isSubmitting}
              >
                Submit
              </button>
            </div>

          </div>
        </div>
        {this.props.questionModels &&
          this.props.questionModels.map(qm => {
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
                      <p><AnswerValue qm={qm} /></p>
                    </div>
                  </div>
                </div>
              )
            );
          })}
        <button
          className="btn btn-primary submit-application mx-auto"
          onClick={this.props.submit}
          disabled={this.props.isSubmitting}
        >
          Submit
        </button>
      </div>
    );
  }
}

class Submitted extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      withdrawModalVisible: false,
      isError: false,
      errorMessage: ""
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

  render() {
    return (
      <div class="submitted">
        <h2>Thank you for applying!</h2>
        {this.state.isError && (
          <div className={"alert alert-danger alert-container"}>
            {this.state.errorMessage}
          </div>
        )}

        <p class="thank-you">
          Thank you for applying to attend {this.props.event ? this.props.event.name : ""}.
          Your application will be reviewed by our committee and we will get back to you as soon as
          possible.
        </p>
        <p class="timestamp">
          You submitted your application on{" "}
          {this.props.timestamp && this.props.timestamp.toLocaleString()}
        </p>
        <div class="submitted-footer">
          <button class="btn btn-danger" onClick={this.handleWithdraw}>
            Withdraw Application
          </button>
        </div>
        <ConfirmModal
          visible={this.state.withdrawModalVisible}
          onOK={this.handleWithdrawOK}
          onCancel={this.handleWithdrawCancel}
          okText={"Yes - Withdraw"}
          cancelText={"No - Don't withdraw"}
        >
          <p>
            By continuing, your submitted application will go into draft state. You MUST press Submit again after you make your changes for your application to be considered in the selection.
          </p>
        </ConfirmModal>
      </div>
    );
  }
}

class ApplicationForm extends Component {
  constructor(props) {
    super(props);

    this.state = {
      formSpec: null,
      isLoading: true,
      isSubmitting: false,
      isError: false,
      isSubmitted: false,
      responseId: null,
      submittedTimestamp: null,
      errorMessage: "",
      errors: [],
      answers: [],
      unsavedChanges: false
    };
  }

  componentDidMount() {
    applicationFormService.getForEvent(this.props.event ? this.props.event.id : 0).then(response => {
      this.setState({
        formSpec: response.formSpec,
        isError: response.formSpec === null,
        errorMessage: response.error,
        isLoading: false,
      });
    });
    this.loadResponse();
  }

  loadResponse = () => {
    applicationFormService.getResponse(this.props.event ? this.props.event.id : 0).then(resp => {
      if (resp.response) {
        this.setState({
          responseId: resp.response.id,
          new_response: false,
          isSubmitted: resp.response.is_submitted,
          submittedTimestamp: resp.response.submitted_timestamp,
          answers: resp.response.answers,
          unsavedChanges: false
        });
      } else {
        this.setState({
          new_response: true,
          unsavedChanges: false
        });
      }
    });
  };

  handleSubmit = event => {
    event.preventDefault();
    this.setState(
      {
        isSubmitting: true
      },
      () => {
        if (this.state.new_response) {
          applicationFormService
            .submit(this.state.formSpec.id, true, this.state.answers)
            .then(resp => {
              let submitError = resp.response_id === null;
              this.setState({
                isError: submitError,
                errorMessage: resp.message,
                isSubmitting: false,
                isSubmitted: resp.is_submitted,
                submittedTimestamp: resp.submitted_timestamp,
                unsavedChanges: false,
                new_response: false,
                responseId: resp.response_id
              });
            });
        } else {
          applicationFormService
            .updateResponse(
              this.state.responseId,
              this.state.formSpec.id,
              true,
              this.state.answers
            )
            .then(resp => {
              let saveError = resp.response_id === null;
              this.setState({
                isError: saveError,
                errorMessage: resp.message,
                isSubmitting: false,
                isSubmitted: resp.is_submitted,
                submittedTimestamp: resp.submitted_timestamp,
                unsavedChanges: false
              });
            });
        }
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
            .submit(this.state.formSpec.id, false, this.state.answers)
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
              this.state.formSpec.id,
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
            .concat(answers)
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

  render() {
    const {
      formSpec,
      isLoading,
      isError,
      isSubmitted,
      errorMessage,
      answers,
      isSubmitting
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

    if (isError) {
      return <div className={"alert alert-danger alert-container"}>{
        errorMessage}
      </div>;
    }

    if (isSubmitted) {
      return (
        <Submitted
          timestamp={this.state.submittedTimestamp}
          onWithdrawn={this.handleWithdrawn}
          responseId={this.state.responseId}
          event={this.props.event}
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
      formSpec.sections &&
      formSpec.sections.slice()
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
              validationError: ""
            };
          })
        };
      });

    const steps =
      sectionModels &&
      sectionModels.map((model, i) => {
        return {
          name: "Step " + i,
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
            />
          )
        };
      });

    const allQuestionModels =
      sectionModels &&
      sectionModels
        .map(section =>
          section.questionModels
            .slice()
            .sort((a, b) => a.question.order - b.question.order)
        )
        .reduce((a, b) => a.concat(b), []);

    steps.push({
      name: "Confirmation",
      component: (
        <Confirmation
          questionModels={allQuestionModels}
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
          />
          <ReactToolTip />
        </div>
        {isSubmitting && <h2 class="submitting">Saving Responses...</h2>}
      </div>
    );
  }
}

export default withRouter(ApplicationForm);
