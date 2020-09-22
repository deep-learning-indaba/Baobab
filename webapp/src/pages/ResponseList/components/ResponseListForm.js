import React, { Component } from 'react';
import '../ResponseList.css';
import { withTranslation } from 'react-i18next';
import { fetchResponse, fetchQuestions } from '../../../services/ResponseList/ResponseList'
import ReactTable from 'react-table';
import "react-table/react-table.css";
import ReactTooltip from 'react-tooltip';


class ResponseListForm extends Component {
    constructor(props) {
        super(props);
        this.state = {
            questions: [],
            selected: [],
            toggleList: false,
            responseTable: null,
            addBtn: {
                background: "hsl(211deg 100% 50%)",
            }
        }
    }


    componentWillMount() {
        this.fetchData()
    }


    fetchData() {
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
            selected: selected,
            addBtn: { background: "hsl(134deg 61% 41%)" }
        }, () => this.fetchData())
    }


    toggleList(list) {
        this.setState({
            toggleList: !list ? true : false
        })
    }


    handleData() {
        // disable question list
        this.toggleList(true)

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
                            handleAnwsers.push(<a key={answer.value[1]} href={answer.value[0]}>{answer.value[1]}</a>)
                        }
                        if (answer.type.includes("choice")) {
                            let choices = [];
                            answer.options.map((opt => {
                                opt.value ? choices.push(<div key={opt.label}><label>{opt.label}</label></div>) : console.log(`${opt.question_id} contains no value`)
                            }))
                            handleAnwsers.push(<div key={choices}>{choices}</div>)
                        }
                        if (answer.type.includes("text")) {
                            handleAnwsers.push(<div>
                                <div key={answer.value} data-tip={answer.value}><p>{answer.value}</p><ReactTooltip
                                    className="Tooltip"
                                />
                                </div>
                                
                            </div>)
                        }
                    }
                })

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

            this.setState({
                responseTable: response,
                addBtn: { background: "hsl(211deg 100% 50%)" }
            }
            )

        })
    }


    generateCol() {
        let colFormat = [];
        let colStyle = {
            'maxWidth': '300',
            'width': '250',
            'whiteSpace': 'normal',
            'maxHeight': '200px',
            'overflow': 'scroll',
            'marginBottom': '10px'
        }

        if (this.state.responseTable) {
            function widthCalc(colItem) {
                if (colItem.includes('Answer')) {
                    return 200
                }
                if (colItem.includes('Review')) {
                    return 180
                }
                else {
                    return 100
                }
            }

            let col = Object.keys(this.state.responseTable[0]);
            col.map(val => {
                colFormat.push({ id: val, Header: val, accessor: val, style: colStyle, width: widthCalc(val) })
            })
        }
        return colFormat
    }



    render() {
        // Translation
        const t = this.props.t;
        // State Obj
        const {
            questions,
            toggleList,
            responseTable,
            addBtn
        } = this.state
        // Generate Col
        const columns = this.generateCol();

        return (
            <section>
                <div className={responseTable ? "question-wrapper wide" : "question-wrapper"}>
                    {/*Heading*/}
                    <h2 className={toggleList || responseTable ? "heading short" : "heading"}>{t('Response List')}</h2>
                    {/*CheckBox*/}
                    <div className="checkbox-top">
                        <input onClick={(e) => this.fetchData()} className="form-check-input input" type="checkbox" value="" id="defaultCheck1" />
                        <label id="label" className="label-top" for="defaultCheck1">
                            {t('Include un-submitted')}
                        </label>
                    </div>

                    {/*DropDown*/}
                    <div className="questions">
                        <button onClick={(e) => this.toggleList(toggleList)} className="btn btn-secondary" type="button" aria-haspopup="true" aria-expanded="false">
                            {t('Questions')}
                        </button>
                        {/*Add Table*/}
                        <button style={addBtn} onClick={(e) => this.handleData()} type="button" className="btn btn-primary">Add Table</button>
                        {toggleList && questions.length && <span style={{ marginLeft: "5px", color: "grey" }}>
                            {questions.length} {t('questions')}
                        </span>}
                        <div className={!toggleList ? "question-list" : "question-list show"}>
                            {questions.length && questions.map(val => {
                                return <div key={val} className="questions-item">
                                    <input onClick={(e) => this.handleSelect(val.question_id)} className="question-list-inputs" type="checkbox" value="" />
                                    <label style={{ marginLeft: "5px" }} className="form-check-label" for="defaultCheck1">
                                        {val.headline}
                                    </label>
                                </div>

                            })
                            }
                        </div>
                    </div>
                </div>

              
                <div className="react-table">
                    {/* Response Table */}
                    {responseTable && !toggleList &&
                        <ReactTable
                        className="ReactTable"
                        data={responseTable}
                        columns={columns}
                        minRows={0} />}
                </div>

            </section>
        )
    }
}

export default withTranslation()(ResponseListForm);
