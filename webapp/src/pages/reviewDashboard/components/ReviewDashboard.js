import React, { Component } from "react";
import { Link } from "react-router-dom";
import ReactTable from "react-table";
import { withRouter } from "react-router";
import "react-table/react-table.css";
import { withTranslation } from 'react-i18next'

import "../ReviewDashboard.css";
import { downloadCSV } from "../../../utils/files";
import { reviewService } from "../../../services/reviews";
// csv-string pulled in Node.js `stream` which is unavailable in the browser.
// This app only uses CSV.stringify on an array-of-arrays, so an inline
// RFC 4180-compliant implementation is sufficient.
const csvStringify = (rows) =>
  rows.map(row =>
    row.map(cell => {
      const s = cell == null ? '' : String(cell);
      return s.includes(',') || s.includes('"') || s.includes('\n')
        ? `"${s.replace(/"/g, '""')}"` : s;
    }).join(',')
  ).join('\n') + '\n';


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
        this.loadReviewList(this.state.mode);
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
                            return score ? score.value : "";
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
        downloadCSV(csvStringify(output), filename);
    }

    handleModeChange = (mode) => {
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
            return (
                <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
                    {error}
                </div>
            );
        }

        const t = this.props.t;

        const columns = [
            {
                id: "response_id",
                Header: <div className="text-left font-bold">{this.props.t("Response ID")}</div>,
                accessor: "response_id",
                filterable: false,
                Cell: this.responseIDCell
            },
            {
                Header: <div className="text-left font-bold">{this.props.t("Candidate")}</div>,
                id: "candidate",
                accessor: r => `${r.response_user_title} ${r.response_user_firstname} ${r.response_user_lastname}`,
                filterable: false,
            }
        ];

        if (this.state.mode === "details") {
            columns.push({
                id: "reviewer",
                Header: <div className="text-left font-bold">{this.props.t("Reviewer")}</div>,
                accessor: r => `${r.reviewer_user_title} ${r.reviewer_user_firstname} ${r.reviewer_user_lastname}`,
                filterable: false,
            });
        }

        if (infoColumns) {
            const formattedInfoColumns = infoColumns.map(col => ({
                ...col,
                Header: <div className="text-left font-bold">{col.Header}</div>
            }));
            columns.push(...formattedInfoColumns)
        }

        columns.push({
            id: "total",
            Header: <div className="text-left font-bold">{this.props.t("Total")}</div>,
            accessor: "total",
        });

        return (
            <div className="bg-white rounded-2xl shadow-sm border border-border p-6 space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/50 pb-4">
                    <h3 className="text-lg font-semibold text-foreground/90">{t("Reviews")}</h3>
                    <div className="inline-flex rounded-lg border border-border p-1 bg-slate-50">
                        <button 
                            type="button"
                            onClick={() => this.handleModeChange("details")}
                            className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors ${this.state.mode === 'details' ? 'bg-white text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                        >
                            {t("Details")}
                        </button>
                        <button 
                            type="button"
                            onClick={() => this.handleModeChange("summary")}
                            className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-colors ${this.state.mode === 'summary' ? 'bg-white text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                        >
                            {t("Summary")}
                        </button>
                    </div>
                </div>

                <div className="react-table">
                    <ReactTable
                        ref={ref => this.ReactTable = ref}
                        loading={isLoading}
                        manual
                        data={reviewList}
                        columns={columns}
                        minRows={0}
                        className="ReactTable"
                    />
                </div>
                
                <div className="flex justify-end pt-2">
                    <button
                        className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-xs font-semibold transition-colors border border-border text-muted-foreground hover:bg-slate-50 cursor-pointer"
                        onClick={() => this.exportToCSV()}
                    >
                        <i className="fas fa-download mr-1.5"></i>
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
        reviewService.getReviewAssignments(this.props.event ? this.props.event.id : 0).then(result => {
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
            return (
                <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
                    {error}
                </div>
            );
        }

        if (loading) {
            return (
                <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            );
        }

        const columns = [
            {
                id: 'fullName',
                Header: <div className="text-left font-bold">{t("Name")}</div>,
                accessor: d => d.user_title + " " + d.firstname + " " + d.lastname
            },
            {
                Header: <div className="text-left font-bold">{t("No. Allocated")}</div>,
                accessor: 'reviews_allocated'
            },
            {
                Header: <div className="text-left font-bold">{t("No. Completed")}</div>,
                accessor: 'reviews_completed'
            },
            {
                id: "percent_complete",
                Header: <div className="text-left font-bold">{t("% Completed")}</div>,
                accessor: u => u.reviews_allocated === 0 ? 100 : (u.reviews_completed / u.reviews_allocated) * 100,
                Cell: props => <div> {props.value.toLocaleString(undefined, { minimumFractionDigits: 1 })} </div>
            }
        ];

        return (
            <div className="bg-white rounded-2xl shadow-sm border border-border p-6 space-y-4">
                <div className="border-b border-border/50 pb-4">
                    <h3 className="text-lg font-semibold text-foreground/90">{t("Reviewers")}</h3>
                </div>
                <div className="react-table">
                    <ReactTable
                        loading={loading}
                        data={reviewers}
                        columns={columns}
                        minRows={0}
                        className="ReactTable"
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

        return (
            <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-8">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                    <div>
                        <h1 className="font-heading text-2xl font-bold text-foreground mb-1">{t("Review Dashboard")}</h1>
                        <p className="text-sm text-muted-foreground">{t("Overview of review assignments and evaluation scoring")}</p>
                    </div>
                    {stage && (
                        <span className="inline-flex items-center px-4 py-2 rounded-xl text-sm font-semibold bg-primary/10 text-primary border border-primary/20">
                            {t("Stage")} {stage.current_stage} / {stage.total_stages}
                        </span>
                    )}
                </div>

                {error && (
                    <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
                        {error}
                    </div>
                )}

                <ReviewAssignment event={this.props.event} />

                <ReviewList event={this.props.event} />
            </div>
        );
    }
}


export default withRouter(withTranslation()(ReviewDashboard));