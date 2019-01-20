import React, { Component } from "react";
import { withRouter } from "react-router";

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

    render() {
        let step = this.state.currentStep;
        return (
            <div class="">
                {this.state.formSpec.sections.map(function(section) {
                    return (
                        <h2>Section {section.name}<br/><small>{section.description}</small></h2>
                    )
                })
                }
            </div>
        )
    }

}

export default withRouter(ApplicationForm)