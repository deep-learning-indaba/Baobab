import React, { Component } from "react";
import { withRouter } from "react-router";
import ReactTable from "react-table";
import { Link } from "react-router-dom";
import "react-table/react-table.css";

import { reviewService } from "../../../services/reviews";
import { Trans, withTranslation } from 'react-i18next'

class ReviewListComponent extends Component {
    constructor(props) {
        super(props);
        this.state = {
            isLoading: true,
            reviewList: [],
            error: null,
            hideSubmitted: false
        }
    }

    componentDidMount() {
        this.loadReviewList();
    }

    processReviewList = (reviewList) => {
        if (!reviewList) {
            return reviewList;
        }

        const columns = [];

        reviewList.forEach(r => {
            r.information.forEach(i => {
                r[i.headline] = i.value;
                if (!columns.some(c=>c === i.headline)) {
                    columns.push(i.headline);
                }
            });
        });

        return {
            reviewList: reviewList,
            columns: columns,
            numReviews: reviewList.length,
            numCompleted: reviewList.filter(r => r.submitted).length
        };
    }

    loadReviewList = () => {
        reviewService
            .getReviewList(this.props.event ? this.props.event.id : 0)
            .then(response => {
                const result = this.processReviewList(response.reviewList);
                const sortedReviewList = result.reviewList.sort((a, b) => a.response_id - b.response_id);
                this.setState({
                    isLoading: false,
                    originalReviewList: sortedReviewList,
                    reviewList: sortedReviewList,
                    infoColumns: result.columns,
                    error: response.error,
                    numReviews: result.numReviews,
                    numCompleted: result.numCompleted
                });
            });
    };

    toggleHideSubmitted = () => {
        this.setState({
            reviewList: !this.state.hideSubmitted ? this.state.originalReviewList.filter(r=>!r.submitted) : this.state.originalReviewList,
            hideSubmitted: !this.state.hideSubmitted
        });
    }

    render() {
        const { error,
            isLoading,
            reviewList,
            infoColumns,
            numReviews,
            numCompleted,
            hideSubmitted
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
                Header: <div className="text-left font-bold">{t("ID")}</div>,
                accessor: "response_id",
                filterable: false,
                width: 100
            },
            {
                Header: <div className="text-left font-bold">{t("Language")}</div>,
                accessor: "language",
                filterable: false,
                width: 100
            }
        ];

        if (infoColumns) {
            infoColumns.forEach(i => {
                columns.push({
                    Header: <div className="text-left font-bold">{i}</div>,
                    accessor: i,
                    filterable: false
                });
            });
        }
        
        const statusCell = props => {
            if (props.original.started && props.original.submitted) {
                return (
                    <div className="flex items-center gap-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-50 text-green-700 border border-green-200/50">{this.props.t("Submitted")}</span>
                        <span className="text-xs text-muted-foreground">{(new Date(props.original.submitted)).toLocaleString("en-GB")}</span>
                    </div>
                );
            }  
            if (props.original.started) {
                return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-warning/10 text-warning-text border border-warning-border/50">{this.props.t("In Progress")}</span>;
            }
            return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">{this.props.t("Not Started")}</span>;
        }

        const actionCell = props => {
            let reviewLink = `/${this.props.event.key}/review/${props.original.response_id}`
            if (props.original.started && props.original.submitted) {
                return <Link to={reviewLink} className="text-primary hover:underline font-semibold">{this.props.t("Edit")}</Link>;
            }
            if (props.original.started) {
                return <Link to={reviewLink} className="text-primary hover:underline font-semibold">{this.props.t("Continue")}</Link>   
            }
            return (
                <Link to={reviewLink} className="text-primary hover:underline font-semibold">{this.props.t("Review")}</Link>
            )
        }

        const totalScoreCell = props => {
            if (props.original.started && props.original.submitted) {
                return <span className="font-bold text-foreground">{props.original.total_score}</span>;
            }
            return "";
        }

        columns.push({
            id: "status",
            Header: <div className="text-left font-bold">{this.props.t("Status")}</div>,
            accessor: r => r.response_id,
            Cell: statusCell
        });

        columns.push({
            id: "score",
            Header: <div className="text-left font-bold">{this.props.t("Total Score")}</div>,
            accessor: "total_score",
            Cell: totalScoreCell,
            width: 120
        });

        columns.push({
            id: "action",
            Header: <div className="text-left font-bold">{this.props.t("Action")}</div>,
            accessor: r => r.response_id,
            Cell: actionCell,
            width: 100
        });

        return (
            <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-6">
                <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6">
                    <div>
                        <h1 className="font-heading text-2xl font-bold text-foreground mb-1">{t("Reviews")}</h1>
                        {numReviews > 0 && numReviews > numCompleted && (
                            <p className="text-sm text-muted-foreground">
                                <Trans>You have {{numReviews}} reviews assigned, of which {{numCompleted}} are completed</Trans>
                            </p>
                        )}
                    </div>
            
                    {numReviews === numCompleted && numReviews > 0 && (
                        <div className="bg-green-50 text-green-800 border border-green-200 p-4 rounded-xl text-sm w-full text-center">
                            {this.props.t("You have completed all your reviews, thank you!")}
                        </div>
                    )}

                    {numReviews === 0 && (
                        <div className="bg-blue-50 text-blue-700 border border-blue-200 p-4 rounded-xl text-sm w-full text-center">
                            {this.props.t("You have no reviews assigned")}
                        </div>
                    )}
                
                    <div className="flex items-center gap-2">
                        <input 
                            onClick={this.toggleHideSubmitted} 
                            checked={hideSubmitted}
                            type="checkbox" 
                            id="defaultCheck1" 
                            className="rounded border-border text-primary focus:ring-primary w-4 h-4 cursor-pointer"
                        />
                        <label htmlFor="defaultCheck1" className="text-sm font-medium text-foreground cursor-pointer select-none">
                            {t("Hide Completed")}
                        </label>
                    </div>

                    <div className="react-table">
                        <ReactTable
                            loading={isLoading}
                            manual
                            data={reviewList}
                            columns={columns}
                            minRows={0}
                            className="ReactTable"
                        />
                    </div>
                </div>
            </div>
          );

    }

}

export default withRouter(withTranslation()(ReviewListComponent));