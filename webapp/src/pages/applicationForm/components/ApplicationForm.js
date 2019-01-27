import React, { Component } from "react";
import { withRouter } from "react-router";
import { applicationFormService } from '../../../services/applicationForm';

class FieldEditor extends React.Component {
    constructor(props) {
      super(props);
      this.handleChange = this.handleChange.bind(this);

      this.state = {}
    }
  
    handleChange(event) {
      const value = event.target.value;
      const id = event.target.id;
      this.props.onChange(id, value);
    }
  
    formControl(id, type, required, choices) {
        switch(type) {
            case "short-text":
                return <input type="text" class="form-control" id={id} name={id} required={required || null} onChange={this.handleChange}/>
            case "single-choice":
                return <input type="checkbox" class="form-control" id={id} name={id} required={required || null} onChange={this.handleChange}/>
            case "long-text":
                return (<textarea class="form-control" rows="5" id={id} name={id} required={required || null} onChange={this.handleChange}></textarea>)
            case "multi-choice":
                return (
                    <select class="form-control" id={id} name={id} required={required || null} onChange={this.handleChange}>
                        {choices.map(function(c) {
                            return (
                                <option>{c}</option>
                            )
                        })}
                    </select>
                )
            case "file":
                return <input type="file" class="form-control-file" id={id} name={id} onChange={this.handleChange}/>
            default:
                return <p className="text-danger">WARNING: No control found for type {type}!</p>
        }
    }

    render() {
        let formId = "question_" + this.props.id;
        return (
            <div class="form-group">            
                <label for={formId}>{this.props.description}</label>
                {this.formControl(formId, this.props.type, this.props.required, this.props.choices)}
            </div>
        )
    }
  }

function Section (props) {
    let questions = props.questions.slice().sort(function(a, b) {
        return a.order - b.order;
    });
    return (
        <div>
            <h2>{props.name}</h2>
            <p>{props.description}</p>
            {questions.map(function(question) {
                    return (
                        <FieldEditor id={question.id} description={question.description} type={question.type} choices={question.choices} required={question.required} onChange={props.onChange}/>
                    )
                })}
        </div>
    )
}

function Confirmation(props) {
    return (
        <div>
            <div class="row">
                <div class="col">
                    <h2>Confirmation</h2>
                    <p>Please confirm that your responses are correct. Use the previous button to correct them if they are not.</p>        
                </div>
            </div>
            {props.answers.map(answer => {
                let question = props.questions.find(question => question.id == answer.questionId);

                return (
                <div>
                    <div class="row">
                        <div class="col">
                            <h4>{question.description}</h4>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col">
                            <p>{answer.value}</p>
                        </div>
                    </div>
                </div>
                )
            })}
        </div>
    )
}

class ApplicationForm extends Component {
    constructor(props) {
        super(props);

        this.state = {
          currentStep: 1,
          formSpec: null,
          isLoading: true,
          answers: []
        };

        this.handleFieldChange = this.handleFieldChange.bind(this);
      }
    
    handleFieldChange(fieldId, value) {
        const questionId = fieldId.substring(fieldId.lastIndexOf('_')+1, fieldId.length);
        const otherAnswers = this.state.answers.filter(answer => answer.questionId != questionId);
        const currentAnswer = {
            "questionId": questionId,
            "value": value
        };
        this.setState({
            answers: otherAnswers.concat(currentAnswer)
        })
    }
    
    componentDidMount() {
        applicationFormService.getForEvent(1).then(formSpec => {
            this.setState({
                formSpec: formSpec,
                isLoading: false
              });
        })
    }

    nextStep = () => {
        let step = this.state.currentStep;
        this.setState({
            currentStep : step + 1
        })
    }

    prevStep = () => {
        let step = this.state.currentStep;
        this.setState({
            currentStep : step - 1
        })
    }

    handleSubmit = event => {
        event.preventDefault();
        applicationFormService.submit(this.state.answers);
    }

    render() {
        const {currentStep, formSpec, isLoading, answers} = this.state;

        if (isLoading) {
            return <img src="data:image/gif;base64,R0lGODlhEAAQAPIAAP///wAAAMLCwkJCQgAAAGJiYoKCgpKSkiH/C05FVFNDQVBFMi4wAwEAAAAh/hpDcmVhdGVkIHdpdGggYWpheGxvYWQuaW5mbwAh+QQJCgAAACwAAAAAEAAQAAADMwi63P4wyklrE2MIOggZnAdOmGYJRbExwroUmcG2LmDEwnHQLVsYOd2mBzkYDAdKa+dIAAAh+QQJCgAAACwAAAAAEAAQAAADNAi63P5OjCEgG4QMu7DmikRxQlFUYDEZIGBMRVsaqHwctXXf7WEYB4Ag1xjihkMZsiUkKhIAIfkECQoAAAAsAAAAABAAEAAAAzYIujIjK8pByJDMlFYvBoVjHA70GU7xSUJhmKtwHPAKzLO9HMaoKwJZ7Rf8AYPDDzKpZBqfvwQAIfkECQoAAAAsAAAAABAAEAAAAzMIumIlK8oyhpHsnFZfhYumCYUhDAQxRIdhHBGqRoKw0R8DYlJd8z0fMDgsGo/IpHI5TAAAIfkECQoAAAAsAAAAABAAEAAAAzIIunInK0rnZBTwGPNMgQwmdsNgXGJUlIWEuR5oWUIpz8pAEAMe6TwfwyYsGo/IpFKSAAAh+QQJCgAAACwAAAAAEAAQAAADMwi6IMKQORfjdOe82p4wGccc4CEuQradylesojEMBgsUc2G7sDX3lQGBMLAJibufbSlKAAAh+QQJCgAAACwAAAAAEAAQAAADMgi63P7wCRHZnFVdmgHu2nFwlWCI3WGc3TSWhUFGxTAUkGCbtgENBMJAEJsxgMLWzpEAACH5BAkKAAAALAAAAAAQABAAAAMyCLrc/jDKSatlQtScKdceCAjDII7HcQ4EMTCpyrCuUBjCYRgHVtqlAiB1YhiCnlsRkAAAOwAAAAAAAAAAAA==" />
        }
        
        const sections = formSpec.sections.slice().sort(function(a, b) {
            return a.order - b.order;
        });
        const allQuestions = sections.flatMap(section => section.questions);

        const numSteps = sections.length;
        
        const style = {
            width : (currentStep / (numSteps+1) * 100) + '%'
        }
        const currentSection = currentStep <= numSteps ? sections[currentStep-1] : null;
        
        return (
            <form onSubmit={this.handleSubmit}>
                <h2>Apply to attend the Deep Learning Indaba 2019</h2>
                <span className="progress-step">{currentSection ? currentSection.name : "Confirmation"}</span>
                <progress className="progress" style={style}></progress>
                
                {currentSection && 
                    <Section name={currentSection.name} description={currentSection.description} questions={currentSection.questions} onChange={this.handleFieldChange}/>
                }
                {!currentSection &&
                    <Confirmation answers={answers} questions={allQuestions}/>
                }
                
                {currentStep > 1 &&
                    <button type="button" class="btn btn-secondary" onClick={this.prevStep}>Previous</button>
                }
                {currentStep <= numSteps &&
                    <button type="button" class="btn btn-primary" onClick={this.nextStep}>Next</button>
                }
                {currentStep > numSteps &&
                    <button type="submit" class="btn btn-primary">Submit</button>
                }
            </form>
        )
    }

}

export default withRouter(ApplicationForm)