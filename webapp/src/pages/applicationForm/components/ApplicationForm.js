import React, { Component } from "react";
import { withRouter } from "react-router";

function Section (props) {
    return (
        <div class="row">
            <div class="col">
                <h2>{props.name}</h2>
                <p>{props.description}</p>
                {props.questions.map(function(question) {
                    return (
                        <p>{question.description}</p>
                    )
                })}
            </div>
        </div>
    )
}

function Confirmation(props) {
    return (
        <div class="row">
            <div class="col">
                <h2>Confirmation</h2>
                <p>Are you sure the answers are correct?</p>
            </div>
        </div>
    )
}

class ApplicationForm extends Component {
    constructor(props) {
        super(props);
    
        let formSpec = {
            "eventId": 1,
            "is_open": true,
            "deadline": "2019-04-30",
            sections: [
                {
                    "sectionId": 1,
                    "name": "Section 1",
                    "description": "Section 1 description",
                    "order": 1,
                    "questions": [
                        {"description": "Question 1", "type": "short-text", "required": true, "order": 1},
                        {"description": "Question 2", "type": "single-choice", "required": false, "order": 2},
                    ]
                },
                {
                    "sectionId": 2,
                    "name": "Section 2",
                    "description": "This is section 2",
                    "order": 2,
                    "questions": [
                        {"description": "What is 2+2?", "type": "short-text", "required": true, "order": 1},
                        {"description": "Upload your CV", "type": "file", "required": false, "order": 2},
                    ]
                },
            ]        
        }

        this.state = {
          currentStep: 1,
          formSpec: formSpec
        };


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
        // Get the values from the form
        // Submit using the applicationFormService
    }

    render() {
        let step = this.state.currentStep;
        let numSteps = this.state.formSpec.sections.length;
        var style = {
            width : (step / (numSteps+1) * 100) + '%'
        }
        let currentSection = step <= numSteps ? this.state.formSpec.sections[step-1] : null;
        return (
            <form onSubmit={this.handleSubmit}>
                <span className="progress-step">{currentSection ? currentSection.name : "Confirmation"}</span>
                <progress className="progress" style={style}></progress>
                
                {currentSection && 
                    <Section name={currentSection.name} description={currentSection.description} questions={currentSection.questions} />
                }
                {!currentSection &&
                    <Confirmation/>
                }
                
                {step > 1 &&
                    <button type="button" class="btn btn-secondary" onClick={this.prevStep}>Previous</button>
                }
                {step <= numSteps &&
                    <button type="button" class="btn btn-primary" onClick={this.nextStep}>Next</button>
                }
                {step > numSteps &&
                    <button type="submit" class="btn btn-primary">Submit</button>
                }
            </form>
        )
    }

}

export default withRouter(ApplicationForm)