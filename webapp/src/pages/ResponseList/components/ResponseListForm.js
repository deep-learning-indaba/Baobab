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
            btnUpdate: false
        }
    }


    componentWillMount() {
        this.fetchData()
        this.handleData()
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
            btnUpdate: true
        }, () => this.fetchData())
    }


    toggleList(list) {
        this.setState({
            toggleList: !list ? true : false
        })
    }


    handleData() {
        const baseUrl = process.env.REACT_APP_API_URL;
        // disable question list
        this.toggleList(true)

        const { selected } = this.state;

        // add Answers or Reviews as new column 
        function addNewCol(row, newAnswers) {
            return row.answers = newAnswers
        }
        // add User Title as new column 
        function userTitleCol(row, user_title, firstname, lastname) {
            return row.user_title = user_title + " " + firstname + " " + lastname
        }


        fetchResponse().then(response => {

            // Handle Answers and Reviews
            response.forEach(val => {
                let handleAnswers = [];
                let handleReviews = [];
                // Check if anwser should be displayed in table based on state.selected, then extract only the value's
                val.answers.forEach(answer => {
                    // format anwers display based on type
                    if (selected.includes(answer.question_id)) {
                        if (answer.type == "file") {
                            handleAnswers.push(<a key={answer.headline} target="_blank" href={baseUrl + "/api/v1/file?filename=" + answer.value}>{answer.headline}</a>)
                        }
                        if (answer.type == "multi-file") {
                            let files = [];
                            answer.value.forEach((file => {
                                file ? files.push(<div key={answer.headline}><a key={answer.headline} target="_blank" href={baseUrl + "/api/v1/file?filename=" + file}>{answer.headline}</a></div>)
                                    :
                                    console.log(`${answer.question_id} contains no value`)
                            }))
                            handleAnswers.push(<div key={answer.headline}>{files}</div>)
                        }
                        if (answer.type.includes("choice")) {
                            let choices = [];
                            answer.options.forEach((opt => {
                                console.log(answer.value)
                                console.log(opt.value)
                                answer.value == opt.value ? choices.push(<div key={opt.label}><label>{opt.label}</label></div>) : console.log(`${opt.question_id} contains no value`)
                            }))
                            handleAnswers.push(<div key={choices}>{choices}</div>)
                        }
                        if (answer.type.includes("text")) {
                            handleAnswers.push(<div>
                                <div key={answer.headline} data-tip={answer.headline}><p>{answer.headline}</p><ReactTooltip
                                    className="Tooltip"
                                />
                                </div>

                            </div>)
                        }
                    }
                })

                // extract only the reviewers name
                val.reviewers.forEach(review => {
                    review ? handleReviews.push(review.reviewer_name) : handleReviews.push("")
                })


                // envoke and store new columns for Reviews and Answers and UserTitle
                let addAnswers = addNewCol(val, handleAnswers);
                let addReviews = addNewCol(val, handleReviews);
                // combine user credentials
                userTitleCol(val, val.user_title, val.firstname, val.lastname)

                // insert Answers values as columns
                if (handleAnswers.length) {
                    console.log("fired")
                    addAnswers.forEach((answer, index) => {
                        let num = (index) + (1);
                        let key = "Answer" + num;
                        val[key] = answer
                    })
                      handleAnswers = [];
                }
                // insert new reviews values as columns
                addReviews.forEach((review, index) => {
                    let num = (index) + (1);
                    let key = "Review" + num;
                    val[key] = review
                    handleReviews = [];
                })
                // delete original review and answer rows as they don't need to be displayed with all their data
                delete val.answers;
                delete val.reviewers;
                delete val.answers;
                delete val.firstname;
                delete val.lastname;
            })

            console.log(response)

            this.setState({
                responseTable: response,
                btnUpdate: false
            }
            )

        })
    }


    generateCols() {
        let colFormat = [];
       
        // Find the row with greatest col count and assign the col values to React Table
        if (this.state.responseTable) {
            function readColumns(rows) {
                let tableColumns = [];
                rows.map(val => {
                    let newColumns = Object.keys(val)
                    tableColumns.length < newColumns.length  ? tableColumns = newColumns : console.log("columns already added")
                })
                
                return tableColumns
            }

            function widthCalc(colItem) {
                if (colItem.includes('Answer')) {
                    return 200
                }

                if (colItem.includes('user') || colItem.includes('Review') || colItem.includes('date')) {
                    return 180
                }
                else {
                    return 100
                }
            }

            let col = readColumns(this.state.responseTable);
            colFormat = col.map( val => ({ id: val, Header: val, accessor: val, class: "myCol", width: widthCalc(val) }))   
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
            btnUpdate
        } = this.state
        // Generate Col
        const columns = this.generateCols();

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
                        {/*Update Table*/}
                        {toggleList && questions.length && <span style={{ marginLeft: "5px", color: "grey" }}>
                            {questions.length} {t('questions')}
                        </span>}
                        <div className={!toggleList ? "question-list" : "question-list show"}>
                            {questions.length && questions.map(val => {
                                return <div key={val} className="questions-item">
                                    <input onClick={(e) => this.handleSelect(val.question_id)} className="question-list-inputs" type="checkbox" value="" id={val.question_id} />
                                    <label style={{ marginLeft: "5px" }} className="form-check-label" for={val.question_id}>
                                        {val.headline}
                                    </label>
                                </div>
                            })
                            }
                        </div>
                        {toggleList && <button
                            onClick={(e) => this.handleData()}
                            type="button"
                            className={btnUpdate ? "btn btn-primary btn-update green" : "btn btn-primary btn-update"}>Update</button>}
                    </div>
                </div>


                <div className="react-table">
                    {/* Response Table */}
                    {!toggleList &&
                        <ReactTable
                            className="ReactTable"
                            data={responseTable ? responseTable : []}
                            columns={columns}
                            minRows={0} />}
                </div>

            </section>
        )
    }
}

export default withTranslation()(ResponseListForm);
