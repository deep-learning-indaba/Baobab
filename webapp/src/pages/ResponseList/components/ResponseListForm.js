import React, { Component } from 'react';
import '../ResponseList.css';
import { withTranslation } from 'react-i18next';
import { fetchResponse, fetchQuestions } from '../../../services/ResponseList/ResponseList'
import ReactTable from 'react-table';
import "react-table/react-table.css";


class ResponseListForm extends Component {

    constructor(props) {
        super(props);
        this.state = {
            questions: [],
            selected: [],
            table: null,
            toggleList: false,
            responseTable: null
        }
    }

    componentWillMount() {
        fetchQuestions().then(response => {
            this.setState({
                questions: response
            })
        })
    }


    handleSelect(question) {
        const selected = this.state.selected;
        let duplicate = selected.indexOf(question)

        if (duplicate == -1) {
            selected.push(question)
        }
        else {
            selected.splice(duplicate, 1)
        }

        this.setState({
            selected: selected
        })
    }

    toggleList(list) {
        this.setState({
            toggleList: !list ? true : false
        })
    }

    addTable(questions) {
        this.setState({
            table: questions
        })
    }


    handleData() {
        const { selected } = this.state;

        // add Answers as new column 
        function addAnswersCol(row, newAnswers) {
            return row.answers = newAnswers
        }
        // add Reviews as new column 
        function addReviewCol(row, newAnswers) {
            return row.answers = newAnswers
        }

        fetchResponse().then(response => {
            let handleAnwsers = [];
            let handleReviews = [];

            // Handle Anwsers and Reviews
            response.map(val => {
                // Check if anwser should be displayed in table based on state.selected, then extract only the value's
                val.answers.map(answer => {
                    // format anwers display based on type
                    if (selected.includes(answer.question_id)) {
                        if (answer.type.includes("file")) {
                            handleAnwsers.push(<a href={answer.value[0]}>{answer.value[1]}</a>)
                        }
                        if (answer.type.includes("choice")) {
                            let choices = [];
                            answer.options.map((opt => {
                                opt.value ? choices.push(<div><label>{opt.label}</label></div>) : console.log(`${opt.question_id} contains no value`)
                            }))
                            handleAnwsers.push(<div>{choices}</div>)
                        }
                        if (answer.type.includes("long-text")) {
                            handleAnwsers.push(<div style={{overflow: "scroll"}}>{answer.value}</div>)
                        }
                    }
                    
                })
                console.log(selected)
                // extract only the reviewers name
                val.reviewers.map(review => {
                    review ? handleReviews.push(review.reviewer_name) : handleReviews.push("")
                })
                // envoke and store new columns for Reviews and Answers
                let addAnwsers = addAnswersCol(val, handleAnwsers);
                let addReviews = addReviewCol(val, handleReviews);

                // insert anwsers values as columns
                if (handleAnwsers.length) {
                    addAnwsers.map((answer, index) => {
                        let num = (index) + (1);
                        let key = "Answer" + num;
                        val[key] = answer
                    })
                }
                // insert new reviews values as columns
                addReviews.map((review, index) => {
                    let num = (index) + (1);
                    let key = "Review" + num;
                    val[key] = review
                })
                // delete original review and answer rows as they don't need to be displayed with all their data
                handleAnwsers = [];
                handleReviews = [];
                delete val.answers;
                delete val.reviewers;
            })

            console.log(response)

            this.setState({
                responseTable: response,
            }
            )

        })
    }


    generateCol() {
        let colFormat = [];
        if (this.state.responseTable) {
            let col = Object.keys(this.state.responseTable[0]);
            col.map(val => {
            console.log(val)
            colFormat.push({ id: val, Header: val, accessor: val, style: { 'whiteSpace': 'unset', 'maxHeight' : '150px', 'maxWidth' : '450px', 'marginBottom': '10px' } })
            })
        }
        return colFormat
    }



    render() {
        const t = this.props.t;
        const {
            questions,
            toggleList,
            responseTable
        } = this.state

        const columns = this.generateCol();


        return (
            <div className="container">

                {/**/}
                {/**/}
                {/**/}
                {/**/}


                {/*CheckBox*/}

                <input onClick={(e) => this.handleData()} className="form-check-input" type="radio" value="" id="defaultCheck1" />
                <label className="form-check-label" for="defaultCheck1">
                    Include un-submitted
                </label>


                {/*DropDown*/}
                <div className="container questions">
                    <button onClick={(e) => this.toggleList(toggleList)} className="btn btn-secondary" type="button" aria-haspopup="true" aria-expanded="false">
                        Questions
                    </button>

                    <div className={!toggleList ? "question-list" : "question-list show"}>
                        {questions.length && questions.map(val => {
                            return <div> <input onClick={(e) => this.handleSelect(val.question_id)} className="form-check-input" type="checkbox" value="" id="defaultCheck1" />
                                <label className="form-check-label" for="defaultCheck1">
                                    {val.headline}
                                </label>
                            </div>

                        })
                        }
                    </div>
                </div>


                {/*Add Table*/}
                <button onClick={(e) => this.handleData()} type="button" className="btn btn-primary">Add Table</button>

                {/* Response Table */}
                {responseTable && <ReactTable
                    data={responseTable}
                    columns={columns}
                    minRows={0} />}

            </div>
        )
    }
}

export default withTranslation()(ResponseListForm);
