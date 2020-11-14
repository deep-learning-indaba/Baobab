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
                if (!columns.some(c=>c == i.headline)) {
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
            return <div className={"alert alert-danger alert-container"}>
                {error}
            </div>;
        }

        const t = this.props.t;

        /*
        'response_id': response.id,
        'language': response.language,
        'information': info,
        'started': review_response is not None,
        'submitted': submitted
        */

        const columns = [
            {
                Header: "ID",
                accessor: "response_id",
                filterable: false,
                width: 100
            },
            {
                Header: this.props.t("Language"),
                accessor: "language",
                filterable: false,
                width: 100
            }
        ];

        if (infoColumns) {
            infoColumns.forEach(i => {
                columns.push({
                    Header: i,
                    accessor: i,
                    filterable: false
                });
            });
        }
        
        const statusCell = props => {
            if (props.original.started && props.original.submitted) {
                return <div><span class="badge badge-success">{this.props.t("Submitted")}</span> <span className="submitted-date">{(new Date(props.original.submitted)).toLocaleString("en-GB")}</span></div>;
            }  
            if (props.original.started) {
                return <span class="badge badge-warning">{this.props.t("In Progress")}</span>;
            }
            return <span class="badge badge-secondary">{this.props.t("Not Started")}</span>;
        }

        const actionCell = props => {
            let reviewLink = `/${this.props.event.key}/review/${props.original.response_id}`
            if (props.original.started && props.original.submitted) {
                return <Link to={reviewLink}>{this.props.t("Edit")}</Link>;
            }
            if (props.original.started) {
                return <Link to={reviewLink}>{this.props.t("Continue")}</Link>   
            }
            return <div>
                <Link to={reviewLink}>{this.props.t("Review")}</Link>
            </div>
        }

        const totalScoreCell = props => {
            if (props.original.started && props.original.submitted) {
                return props.original.total_score;
            }
            return "";
        }

        columns.push({
            id: "status",
            Header: this.props.t("Status"),
            accessor: r => r.response_id,
            Cell: statusCell
        });

        columns.push({
            id: "score",
            Header: this.props.t("Total Score"),
            accessor: "total_score",
            Cell: totalScoreCell,
            width: 100
        });

        columns.push({
            id: "action",
            Header: this.props.t("Action"),
            accessor: r => r.response_id,
            Cell: actionCell,
            width: 100
        });

        return (
            <div className="review-list-container">
              <h2 className="title">{t("Reviews")}</h2>
              {numReviews > 0 && numReviews > numCompleted && 
                <p class="summary"><Trans>You have {{numReviews}} reviews assigned, of which {{numCompleted}} are completed</Trans></p>}
      
              {numReviews === numCompleted && numReviews > 0 && 
                <div className="alert alert-success">{this.props.t("You have completed all your reviews, thank you!")}</div>}

              {numReviews == 0 && 
                <div className="alert alert-info">{this.props.t("You have no reviews assigned")}</div>}
            
              <div class="checkbox-top">
                  <input onClick={(e) => this.toggleHideSubmitted()} className="form-check-input input" type="checkbox" value={hideSubmitted} id="defaultCheck1" />
                  <label id="label" class="label-top" for="defaultCheck1">{t("Hide Completed")}</label>
              </div>

              <div className={"review-padding"}>
                <ReactTable
                  loading={isLoading}
                  manual
                  data={reviewList}
                  columns={columns}
                  minRows={0} />
              </div>
            </div>
          );

    }

}

export default withRouter(withTranslation()(ReviewListComponent));