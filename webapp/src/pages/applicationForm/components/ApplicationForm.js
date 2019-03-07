import React, { Component } from "react";
import { withRouter } from "react-router";
import { applicationFormService } from "../../../services/applicationForm";
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import FormTextArea from "../../../components/form/FormTextArea";
import ReactToolTip from "react-tooltip";
import { ConfirmModal } from "react-bootstrap4-modal";
import StepZilla from "react-stepzilla";

const DEFAULT_EVENT_ID = process.env.DEFAULT_EVENT_ID || 1;

const SHORT_TEXT = "short-text";
const SINGLE_CHOICE = "single-choice";
const LONG_TEXT = ["long-text", "long_text"];
const MULTI_CHOICE = "multi-choice";
const FILE = "file";

class FieldEditor extends React.Component {
  constructor(props) {
    super(props);
    this.id = "question_" + props.question.id;
  }

  handleChange = event => {
    const value = event.target.value;
    if (this.props.onChange) {
      this.props.onChange(this.props.question, value);
    }
  };

  handleChangeDropdown = (name, dropdown) => {
    if (this.props.onChange) {
      this.props.onChange(this.props.question, dropdown.value);
    }
  };

  formControl = (key, question, answer, validationError) => {
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
          <FormTextBox
            Id={this.id}
            name={this.id}
            type="file"
            label={question.description}
            placeholder={answer || question.placeholder}
            onChange={this.handleChange}
            key={"i_" + key}
            showError={validationError}
            errorText={validationError}
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

  render() {
    return (
      <div className={"question"}>
        <h4>{this.props.question.headline}</h4>
        {this.formControl(
          this.props.key,
          this.props.question,
          this.props.answer ? this.props.answer.value : null,
          this.props.validationError
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

  updateQuestionModelState = (question, apply) => {
    const newQuestionModels = this.state.questionModels.map(q => {
      if (q.question.id !== question.id) {
        return q;
      }
      return apply(q);
    });
    this.setState({
      questionModels: newQuestionModels
    });
  };

  onChange = (question, value) => {
    const newAnswer = {
      question_id: question.id,
      value: value
    };

    const newQuestionModels = this.state.questionModels.map(q => {
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
    });

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
        validationStale: false
      },
      () => {
        if (this.props.answerChanged && isValid) {
          this.props.answerChanged(
            this.state.questionModels.map(q => q.answer).filter(a => a)
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

  render() {
    const {
      section,
      questionModels,
      hasValidated,
      validationStale
    } = this.state;
    return (
      <div className={"section"}>
        <div className={"headline"}>
          <h2>{section.name}</h2>
          <p>{section.description}</p>
        </div>
        {questionModels &&
          questionModels.map(model => (
            <FieldEditor
              key={model.question.id}
              question={model.question}
              answer={model.answer}
              validationError={model.validationError}
              onChange={this.onChange}
            />
          ))}
        {this.props.unsavedChanges && !this.props.isSaving && (
          <a href="#" class="save mx-auto" onClick={this.handleSave}>
            Save for later...
          </a>
        )}
        {this.props.isSaving && <span class="saving mx-auto">Saving...</span>}
        {hasValidated && !validationStale && (
          <div class="alert alert-danger">
            Please fix the errors before continuing.
          </div>
        )}
      </div>
    );
  }
}

function Confirmation(props) {
  return (
    <div>
      <div class="row">
        <div class="col confirmation-heading">
          <h2>Confirmation</h2>
          <p>
            Please confirm that your responses are correct. Use the previous
            button to correct them if they are not.
          </p>
        </div>
      </div>
      {props.questionModels &&
        props.questionModels.map(qm => {
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
                    <p>{qm.answer ? qm.answer.value : "No answer provided."}</p>
                  </div>
                </div>
              </div>
            )
          );
        })}
      <button
        class="btn btn-primary submit-application mx-auto"
        onClick={props.submit}
      >
        Submit
      </button>
    </div>
  );
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
          <div className={"alert alert-danger"}>{this.state.errorMessage}</div>
        )}

        <p class="thank-you">
          Thank you for applying to attend The Deep Learning Indaba 2019,
          Kenyatta University, Nairobi, Kenya . Your application is being
          reviewed by our committee and we will get back to you as soon as
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
            Are you SURE you want to withdraw your application to the Deep
            Learning Indaba 2019? You will NOT be considered for a place at the
            Indaba if you continue.
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
    applicationFormService.getForEvent(DEFAULT_EVENT_ID).then(response => {
      this.setState({
        formSpec: response.formSpec,
        isError: response.formSpec === null,
        errorMessage: response.message,
        isLoading: false
      });
    });
    this.loadResponse();
  }

  loadResponse = () => {
    applicationFormService.getResponse(DEFAULT_EVENT_ID).then(resp => {
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
                isSaving: false
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

  handleAnswerChanged = answers => {
    if (answers) {
      this.setState(prevState => {
        return {
          answers: prevState.answers
            .filter(a => !answers.includes(a.question_id))
            .concat(answers)
        };
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
    if (isLoading) {
      return (
        <img
          class="loading-indicator mx-auto"
          src="data:image/gif;base64,R0lGODlhEAAQAPIAAP///wAAAMLCwkJCQgAAAGJiYoKCgpKSkiH/C05FVFNDQVBFMi4wAwEAAAAh/hpDcmVhdGVkIHdpdGggYWpheGxvYWQuaW5mbwAh+QQJCgAAACwAAAAAEAAQAAADMwi63P4wyklrE2MIOggZnAdOmGYJRbExwroUmcG2LmDEwnHQLVsYOd2mBzkYDAdKa+dIAAAh+QQJCgAAACwAAAAAEAAQAAADNAi63P5OjCEgG4QMu7DmikRxQlFUYDEZIGBMRVsaqHwctXXf7WEYB4Ag1xjihkMZsiUkKhIAIfkECQoAAAAsAAAAABAAEAAAAzYIujIjK8pByJDMlFYvBoVjHA70GU7xSUJhmKtwHPAKzLO9HMaoKwJZ7Rf8AYPDDzKpZBqfvwQAIfkECQoAAAAsAAAAABAAEAAAAzMIumIlK8oyhpHsnFZfhYumCYUhDAQxRIdhHBGqRoKw0R8DYlJd8z0fMDgsGo/IpHI5TAAAIfkECQoAAAAsAAAAABAAEAAAAzIIunInK0rnZBTwGPNMgQwmdsNgXGJUlIWEuR5oWUIpz8pAEAMe6TwfwyYsGo/IpFKSAAAh+QQJCgAAACwAAAAAEAAQAAADMwi6IMKQORfjdOe82p4wGccc4CEuQradylesojEMBgsUc2G7sDX3lQGBMLAJibufbSlKAAAh+QQJCgAAACwAAAAAEAAQAAADMgi63P7wCRHZnFVdmgHu2nFwlWCI3WGc3TSWhUFGxTAUkGCbtgENBMJAEJsxgMLWzpEAACH5BAkKAAAALAAAAAAQABAAAAMyCLrc/jDKSatlQtScKdceCAjDII7HcQ4EMTCpyrCuUBjCYRgHVtqlAiB1YhiCnlsRkAAAOwAAAAAAAAAAAA=="
        />
      );
    }

    if (isError) {
      return <div className={"alert alert-danger"}>{errorMessage}</div>;
    }

    if (isSubmitted) {
      return (
        <Submitted
          timestamp={this.state.submittedTimestamp}
          onWithdrawn={this.handleWithdrawn}
          responseId={this.state.responseId}
        />
      );
    }

    const sections =
      formSpec.sections &&
      formSpec.sections.slice().sort((a, b) => a.order - b.order);
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
              key={model.section.id}
              section={model.section}
              questionModels={model.questionModels}
              answerChanged={this.handleAnswerChanged}
              save={this.handleSave}
              changed={() => this.setState({ unsavedChanges: true })}
              unsavedChanges={this.state.unsavedChanges}
              isSaving={this.state.isSaving}
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
