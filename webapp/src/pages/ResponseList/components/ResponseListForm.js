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
        }, () => {
            this.apiCall()
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
        // formatAnswers
        function formatAnswers(row, newAnswers) {
            return row.answers = newAnswers
        }
        // formatReviews
        function formatReview(row, newAnswers) {
            return row.answers = newAnswers
        }

        fetchResponse().then(response => {
            let handleAnwsers = [];
            let handleReviews = [];

            // Handle Anwsers
            response.map(val => {
                val.answers.map(answer => {
                    handleAnwsers.push(answer.value)
                })

                val.reviewers.map(review => {
                    review ? handleReviews.push(review.reviewer_name) : handleReviews.push("")
                })

                let formatAnwsers = formatAnswers(val, handleAnwsers);
                let formatReviews = formatReview(val, handleReviews);
                handleAnwsers = [];
                handleReviews = [];
                val.answers = formatAnwsers;
                delete val.reviewers;
                formatReviews.map((review, index) => {
                    let n = "Review" + index;
                    val[n] = review
                })
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
                colFormat.push({ id: val, Header: val, accessor: val })
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
                                    {val.type}
                                </label>
                            </div>

                        })
                        }
                    </div>
                </div>


                {/*Add Table*/}
                <button onClick={(e) => this.addTable(questions)} type="button" className="btn btn-primary">Add Table</button>

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
