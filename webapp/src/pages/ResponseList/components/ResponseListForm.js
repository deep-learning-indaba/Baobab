import React, { Component } from 'react';
import '../ResponseList.css';
import { withTranslation } from 'react-i18next';
import { questions, response } from '../../../services/responseList/responseList.service'
import ReactTable from 'react-table';
import "react-table/react-table.css";
import ReactTooltip from 'react-tooltip';
import { NavLink } from "react-router-dom";
import { tagList } from '../../../services/taglist/tagList.service'


class ResponseListForm extends Component {
    constructor(props) {
        super(props);
        this.state = {
            questions: [],
            selectedQuestions: [],
            toggleList: false,
            responseTable: null,
            btnUpdate: false,
            selectedTags: [],
        }
    }


    componentWillMount() {
        this.fetchTags();
        this.handleData();
        this.fetchQuestions();
    }

    // Fetch Tags
    fetchTags() {
        tagList.list().then(response => {
            this.setState({
                tags: response
            })
        })
    }


    // Fetch Questions
    fetchQuestions() {
        questions().then(response => {
            this.setState({
                questions: response
            })
        })
    }



    // Fetch Ressponses and Handle/Format Data
    handleData() {
        const baseUrl = process.env.REACT_APP_API_URL;
        const { selectedTags, selectedQuestions } = this.state

        // disable question list
        this.toggleList(false)

        response(selectedTags).then(response => {
            // Handle Answers and Reviews
            response.forEach(val => {
                let handleAnswers = [];
                let handleReviews = [];
                let handleTags = [];

                // Create Response Id Link
                if (this.props.event) {
                    val.response_id = <NavLink
                        to={`${this.props.event.key}/responsePage/${val.response_id}`}
                        className="table-nav-link"
                    >
                        {val.response_id}
                    </NavLink>;
                }

                // Check if anwser should be displayed in table based on state.selected, then extract only the value's
                val.answers.forEach(answer => {
                    // format anwers display based on type
                    if (selectedQuestions.includes(answer.question_id)) {
                        if (answer.type.includes("text")) {
                            handleAnswers.push([{
                                headline: answer.headline, value: <div key={answer.headline} data-tip={answer.value}><p>{answer.value}</p><ReactTooltip
                                    className="Tooltip"
                                />
                                </div>
                            }])
                        }

                        else if (answer.type == "file") {
                            handleAnswers.push([{
                                headline: answer.headline,
                                value: <a key={answer.headline} target="_blank" href={baseUrl + "/api/v1/file?filename=" + answer.value}>{answer.value}</a>
                            }])
                        }

                        else if (answer.type == "multi-file") {
                            let files = [];
                            answer.value.forEach((file => {
                                if (file) {
                                    files.push(
                                        <div key={answer.headline}><a key={answer.headline} target="_blank" href={baseUrl + "/api/v1/file?filename=" + file}>{answer.value}</a></div>
                                    )
                                }
                            }))
                            handleAnswers.push([{ headline: answer.headline, value: <div key={answer.headline}>{files}</div> }])
                        }

                        else if (answer.type.includes("choice")) {
                            let choices = [];
                            answer.options.forEach((opt => {
                                if (answer.value == opt.value) { choices.push(<div key={opt.label}><label>{opt.label}</label></div>) }
                            }))
                            handleAnswers.push([{ headline: answer.headline, value: <div key={choices}>{choices}</div> }])
                        }

                        else {
                            handleAnswers.push([{
                                headline: answer.headline, value: <div key={answer.headline}><p>{answer.value}</p>
                                </div>
                            }])
                        }
                    }
                })

                // extract only the tag names
                val.tags.forEach(tag => {
                    if (tag) {
                        handleTags.push(<div>{tag.name}</div>)
                    }
                })

                // extract only the reviewers name
                val.reviewers.forEach(review => {
                    review ? handleReviews.push(review.reviewer_name) : handleReviews.push("");
                })

                // add User Title as new column 
                function userTitleCol(row, user_title, firstname, lastname) {
                    return row.user_title = user_title + " " + firstname + " " + lastname
                }

                // envoke and store new columns for UserTitle
                // combine user credentials
                userTitleCol(val, val.user_title, val.firstname, val.lastname);

                // insert Answers values as columns
                if (handleAnswers.length) {
                    handleAnswers.forEach((answer, index) => {
                        let key = answer[0].headline
                        val[key] = answer[0].value
                    });
                    handleAnswers = [];
                };
                // insert new reviews values as columns
                if (handleReviews.length) {
                    handleReviews.forEach((review, index) => {
                        let num = (index) + (1);
                        let key = "Review" + num;
                        val[key] = review
                        handleReviews = [];
                    })
                };

                val.tags = handleTags
                // delete original review and answer rows as they don't need to be displayed with all their data
                delete val.answers;
                delete val.reviewers;
                delete val.firstname;
                delete val.lastname;

            })

            this.setState({
                responseTable: response,
                btnUpdate: false,
            })
        })
    }

    // Tag Selection State
    tagSelector(name) {
        const list = this.state.selectedTags;
        const duplicateTag = list.indexOf(name) // test against duplicates

        duplicateTag == -1 ? list.push(name) : list.splice(duplicateTag, 1);

        this.setState({
            selectedTags: list,
            btnUpdate: true
        })
    }

    // Delete Pill function
    deletePill(val) {
        this.tagSelector(val);
        this.handleData()
    }


    // Question selection state
    questionSelector(question) {
        const selected = this.state.selectedQuestions;
        let duplicate = selected.indexOf(question)

        duplicate == -1 ? selected.push(question) : selected.splice(duplicate, 1);
        this.setState({
            selectedQuestions: selected,
            btnUpdate: true
        })
    }


    // Toggle List
    toggleList(list, type) {
        this.setState({
            toggleList: !list ? type : false
        })
    }


    // Generate table columns
    generateCols() {
        let colFormat = [];
        // Find the row with greatest col count and assign the col values to React Table
        if (this.state.responseTable) {

            // function
            function readColumns(rows) {
                let tableColumns = [];
                rows.map(val => {
                    let newColumns = Object.keys(val);
                    newColumns.forEach(val => {
                        if (!tableColumns.includes(val)) {
                            tableColumns.push(val)
                        };
                    });
                });
                return tableColumns
            };

            // function
            function widthCalc(colItem) {
                if (colItem.includes('question')) {
                    return 200
                };

                if (colItem.includes('user') || colItem.includes('Review') || colItem.includes('date')) {
                    return 180
                }
                else {
                    return 100
                }
            }

            let col = readColumns(this.state.responseTable);
            colFormat = col.map(val => ({ id: val, Header: val, accessor: val, className: "myCol", width: widthCalc(val) }));
        }

        return colFormat
    }



    renderReset() {
        const {
            selectedQuestions,
            toggleList,
            selectedTags,
        } = this.state
        if (!toggleList) {
            if (selectedTags.length || selectedQuestions.length) {
            return  <button onClick={(e) => this.reset(e)} className="btn btn-primary">Reset</button>
        }
    }
    }



    // Reset state, question and tag list UI 
    reset() {
        // reset checkboxes
        document.querySelectorAll('input[type=checkbox]').forEach(el => el.checked = false);

        // disable question list
        this.toggleList(true)

        this.setState({
            selectedQuestions: [],
            selectedTags: []
        }, () => this.handleData())
    }



    render() {
        // Translation
        const t = this.props.t;
        // State values
        const {
            questions,
            toggleList,
            responseTable,
            btnUpdate,
            tags,
            selectedTags,
            selectedQuestions
        } = this.state
        // Generate Col
        const columns = this.generateCols();
        const renderReset = this.renderReset();

        return (
            <section className="response-list-wrapper">
                <div className={responseTable ? "question-wrapper wide" : "question-wrapper"}>
                    {/*Heading*/}
                    <h2 className={toggleList || responseTable ? "heading short" : "heading"}>{t('Response List')}</h2>
                    {/*CheckBox*/}
                    <div className="checkbox-top">
                        <input onClick={(e) => this.fetchQuestions()} className="form-check-input input" type="checkbox" value="" id="defaultCheck1" />
                        <label id="label" className="label-top" htmlFor="defaultCheck1">
                            {t('Include un-submitted')}
                        </label>
                    </div>



                    {/* Wrapper for drop down lists */}
                    <div className="lists-wrapper">


                        {/*Tags Dropdown*/}
                        <div className="tags">
                            {toggleList == "tag" ?  <button
                                onClick={(e) => this.handleData(selectedTags)}
                                type="button"
                                className="btn btn-success">Update</button> :
                                <button onClick={(e) => this.toggleList(toggleList, "tag")}
                                    className={toggleList == "question" ? "btn tag hide" : "btn tag"}
                                    type="button"
                                    aria-haspopup="true"
                                    aria-expanded="false">
                                {t('Tags')}
                            </button>
                             }
                        </div>

                        {/*Questions DropDown*/}
                        <div className="questions">
                            { toggleList == "question" ? 
                         <button
                            onClick={(e) => this.handleData(selectedTags)}
                            type="button"
                            className={toggleList ==  "tag" ? "btn btn-success hide" : "btn btn-success"}
                            >Update</button>

                         :  <button onClick={(e) => this.toggleList(toggleList, "question")} className={toggleList ==  "tag" ? "btn btn-secondary hide" : "btn btn-secondary"}
                                type="button" aria-haspopup="true" aria-expanded="false">
                                {t('Questions')}
                            </button>}
                           

                            {/* Reset Button */}
                            {renderReset}
                          
                            {/*Update Table*/}
                            {toggleList == "question" && questions.length && <span style={{ marginLeft: "5px", color: "grey" }}>
                                {questions.length} {t('questions')}
                            </span>}
                        </div>


                        {/*Pills*/}
                        <div class="pills">
                            {selectedTags &&
                                selectedTags.map(val => {
                                    return <span onClick={(e) => this.deletePill(val)} className="badge badge-primary">{val} <i className="far fa-trash-alt"></i></span>
                                })
                            }
                        </div>

                    </div>


                    {/* List Section */}
                    <div className="list-section">

                        {/*Tag List*/}
                        <div className={toggleList == "tag" ? "tag-list show" : "tag-list"}>
                            {tags &&
                                tags.map(val => {
                                    return <div className={selectedTags.includes(val.name) ? "tag-item hide" : "tag-item"} key={val.id} >
                                        <button className="btn tags" onClick={(e) => this.tagSelector(val.name)}>{val.name}</button>
                                    </div>
                                })}
                            {/* Update Button */}
                          
                        </div>

                        {/* List Questions */}
                        <div className={toggleList == "question" ? "question-list show" : "question-list "}>
                            {questions.length && questions.map(val => {
                                return <div className={selectedQuestions.includes(val.question_id) ? "questions-item hide" : "questions-item"} key={val.headline + "" + val.value} >
                                    <input onClick={(e) => this.questionSelector(val.question_id)} className="question-list-inputs" type="checkbox" value="" id={val.question_id} />
                                    <label style={{ marginLeft: "5px" }} className="form-check-label" htmlFor={val.question_id}>
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
                    {!toggleList &&
                        <ReactTable
                            className="ReactTable"
                            data={responseTable ? responseTable : []}
                            columns={columns}
                            minRows={0}
                        />
                    }
                </div>

            </section>
        )
    }
}

export default withTranslation()(ResponseListForm);