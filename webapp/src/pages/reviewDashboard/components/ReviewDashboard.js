import React, { Component } from "react";
import { Link } from "react-router-dom";
import ReactTable from "react-table";
import { withRouter } from "react-router";
import "react-table/react-table.css";
import { withTranslation } from 'react-i18next'

import "../ReviewDashboard.css";
import { downloadCSV } from "../../../utils/files";
import { reviewService } from "../../../services/reviews";
import Loading from "../../../components/Loading";
import * as CSV from 'csv-string';


class ReviewListComponent extends Component {
    constructor(props) {
        super(props);
        this.state = {
            error: null,
            infoColumns: [],
            isLoading: true,
            reviewList: [],
            mode: "details"
        }
    }

    componentDidMount() {
        console.log('got to load', this.props)
        this.loadReviewList(this.state.mode);
        console.log('loaded')
    }

    responseIDCell = props => {
        const reviewLink = `/${this.props.event.key}/review/${props.value}`
        return <Link to={reviewLink}>{props.value}</Link>;
    }

    processReviewList = (reviewList) => {
        if (!reviewList) {
            return reviewList;
        }

        const columns = [];

        reviewList.forEach(row => {
            row.identifiers.forEach(i => {
                if (!columns.some(c => c.Header === i.headline)) {
                    columns.push({
                        id: i.headline,
                        Header: i.headline,
                        accessor: r => {
                            const identifier = r.identifiers.find(x => x.headline === i.headline);
                            return identifier ? identifier.value : "";
                        }
                    });
                }
            });
        });

        reviewList.forEach(row => {
            row.scores.forEach(i => {
                const headline = `${i.headline ? i.headline + '; ' : ''}${i.description ? i.description : ''}`
                const id = `review_question${i.review_question_id}`
                if (!columns.some(c => c.id === id)) {
                    columns.push({
                        id: id,
                        Header: headline,
                        accessor: r => {
                            const score = r.scores.find(s => s.review_question_id === i.review_question_id);
                            return score ? score.score : "";
                        }
                    });
                }
            });
        });

        return {
            columns: columns,
            reviewList: reviewList,
        };
    }

    loadReviewList = (mode) => {
        const eventId = this.props.event ? this.props.event.id : 0;
        const promise = mode === "details" ? reviewService.getReviewDetails(eventId) : reviewService.getReviewSummaryList(eventId);

        this.setState({
            loading: true,
            error: null
        });

        promise.then(response => {
            if (response.error) {
                this.setState({
                    isLoading: false,
                    error: response.error
                });
                return;
            }
            const result = this.processReviewList(response.reviewList);
            const sortedReviewList = result.reviewList.sort((a, b) => a.response_id - b.response_id);
            this.setState({
                isLoading: false,
                reviewList: sortedReviewList,
                infoColumns: result.columns,
                error: response.error,
            });
        });
    };

    exportToCSV() {
        const getResolvedState = this.ReactTable.getResolvedState();
        const columns = getResolvedState.columns;
        const rows = getResolvedState.resolvedData;
        
        const output = [
            columns.map(c => c.Header)
        ];

        output.push(
            ...rows.map(row =>
                columns.map(col => {
                    if (row.hasOwnProperty(col.Header)) {
                        return row[col.Header];   // row is mapped by column header
                    } else if (row.hasOwnProperty(col.id)) {
                        return row[col.id];  // row is mapped by column id (accessor is a function)
                    } else {
                        return row[col.accessor];  // row is directly mapped to accessor by string property
                    }
                })
            )
        );
        
        const filename = `review_${this.state.mode}_` + new Date().toDateString().split(" ").join("_") + ".csv";
        downloadCSV(CSV.stringify(output), filename);
    }

    modeChange = event => {
        const mode = event.currentTarget.querySelector("input").value;
        console.log("Changing mode to " + mode);
        const prevMode = this.state.mode;
        if (prevMode !== mode) {
            this.loadReviewList(mode);
        }

        this.setState({
            mode: mode
        });
    }

    render() {
        const {
            error,
            isLoading,
            infoColumns,
            reviewList
        } = this.state;

        if (error) {
            return <div className={"alert alert-danger alert-container"}>
                {error}
            </div>;
        }

        const t = this.props.t;

        const columns = [
            {
                id: "response_id",
                Header: this.props.t("Response ID"),
                accessor: "response_id",
                filterable: false,
                Cell: this.responseIDCell
            },
            {
                Header: this.props.t("Candidate"),
                id: "candidate",
                accessor: r => `${r.response_user_title} ${r.response_user_firstname} ${r.response_user_lastname}`,
                filterable: false,
            }
        ];

        if (this.state.mode === "details") {
            columns.push({
                id: "reviewer",
                Header: this.props.t("Reviewer"),
                accessor: r => `${r.reviewer_user_title} ${r.reviewer_user_firstname} ${r.reviewer_user_lastname}`,
                filterable: false,
            });
        }

        if (infoColumns) {
            columns.push(...infoColumns)
        }

        columns.push({
            id: "total",
            Header: this.props.t("Total"),
            accessor: "total",
        });

        return (
            <div className="card">
                <div className="card-body text-center">
                    <h3 className="card-title">{t("Reviews")}</h3>
                    <div class="btn-group btn-group-toggle" data-toggle="buttons">
                        <label class="btn btn-primary active" onClick={this.modeChange}>
                            <input type="radio" name="mode" id="detailsRadio" value="details" defaultChecked /> {t("Details")}
                        </label>
                        <label class="btn btn-primary" onClick={this.modeChange}>
                            <input type="radio" name="mode" id="summaryRadio" value="summary" /> {t("Summary")}
                        </label>
                    </div>

                    <div className={"review-padding"}>
                        <ReactTable
                            ref={ref => this.ReactTable = ref}
                            loading={isLoading}
                            manual
                            data={reviewList}
                            columns={columns}
                            minRows={0}
                        />
                    </div>
                    <br />
                    <button
                        className="pull-right btn btn-primary btn-sm"
                        onClick={() => this.exportToCSV()}
                    >
                        {this.props.t("Download csv")}
                    </button>
                </div>
            </div>
        );
    }
}

const ReviewList = withRouter(withTranslation()(ReviewListComponent));


class ReviewAssignmentComponent extends Component {
    constructor(props) {
        super(props);
        this.state = {
            loading: true,
            reviewers: null,
            error: "",
        };
    }

    componentDidMount() {
        reviewService.getReviewAssignments(this.props.event ? this.props.event.id : 0, this.props.match.params.id).then(result => {
            this.setState({
                loading: false,
                reviewers: result.reviewers,
                error: result.error,
            });
        });
    }

    render() {
        const { loading, reviewers, error } = this.state;
        const t = this.props.t;

        if (error) {
            return <div class="alert alert-danger alert-container">{error}</div>
        }

        if (loading) {
            return <Loading />
        }

        const columns = [
            {
                id: 'fullName',
                Header: t("Name"),
                accessor: d => d.user_title + " " + d.firstname + " " + d.lastname
            },
            {
                Header: t("No. Allocated"),
                accessor: 'reviews_allocated'
            },
            {
                Header: t("No. Completed"),
                accessor: 'reviews_completed'
            }
        ];

        return (
            <div className="card">
                <div className="card-body">
                    <h3 className="card-title">{t("Reviewers")}</h3>
                    <ReactTable
                        loading={loading}
                        manual
                        data={reviewers}
                        columns={columns}
                        minRows={0}
                    />
                </div>
            </div>
        )

    }
}

const ReviewAssignment = withRouter(withTranslation()(ReviewAssignmentComponent));

class ReviewDashboard extends Component {
    constructor(props) {
        super(props);
        this.state = {
            stage: null,
            error: ""
        };
    }

    componentDidMount() {
        reviewService.getReviewStage(this.props.event.id).then(response => {
            this.setState({
                stage: response.data,
                error: response.error
            });
        });
    }

    render() {
        const t = this.props.t;
        const { stage, error } = this.state;
        /*
        TODO:
            - Add summary of assigned and completed reviews
            - Make cards collapsable
            - Add buttons to advance reviews to next stage (check for incomplete reviews!)
        */

        return (
            <div className="review-list-container">
                <h2 className="title">
                    {t("Review Dashboard")}
                    {stage && <span className="pull-right text-primary"><h2 className="stage-info text-center">{t("Stage")} {stage.current_stage} / {stage.total_stages}</h2></span>}
                </h2>
                {error && <div className="alert alert-danger">{error}</div>}

                <ReviewAssignment event={this.props.event} />

                <ReviewList event={this.props.event} />
            </div>
        );
    }
}


export default withRouter(withTranslation()(ReviewDashboard));