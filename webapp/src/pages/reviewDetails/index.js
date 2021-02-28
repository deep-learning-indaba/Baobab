import React, { Component } from "react";
import { Link } from "react-router-dom";
import ReactTable from "react-table";
import { withRouter } from "react-router";
import "react-table/react-table.css";

import { reviewService } from "../../services/reviews";
import { withTranslation } from 'react-i18next'

class ReviewDetailsPage extends Component {
    constructor(props) {
        super(props);
        this.state = {
            error: null,
            infoColumns: [],
            isLoading: true,
            reviewDetails: [],
        }
    }

    componentDidMount() {
        this.loadReviewDetails();
    }

    responseIDCell = props => {
        let reviewLink = `/${this.props.event.key}/review/${props.value}`
        return <Link to={reviewLink}>{props.value}</Link>;
    }

    identifierCell = props => {
        const row = props.original.identifiers.find(i => i.headline === props.column.Header);
        return row.value;
    }

    scoreCell = props => {
        const row = props.original.scores.find(i => {
            const header = `${i.headline ? i.headline + '; ' : '' }${i.description ? i.description : ''}`
            return header === props.column.Header
        });
        return row.score;
    }

    processReviewDetails = (reviewDetails) => {
        if (!reviewDetails) {
            return reviewDetails;
        }

        const columns = [];

        reviewDetails.forEach(r => {
            r.identifiers.forEach(i => {
                if (!columns.some(c => c.Header == i.headline )) {
                    columns.push({
                        id: i.headline,
                        Header: i.headline,
                        accessor: r => r.response_id,
                        Cell: this.identifierCell
                    });
                }
            });
        });

        reviewDetails.forEach(r => {
            r.scores.forEach(i => {
                const headline = `${i.headline ? i.headline + '; ' : '' }${i.description ? i.description : ''}`
                if (!columns.some(c => c.Header == headline)) {
                    columns.push({
                        id: headline,
                        Header: headline,
                        accessor: r => r.response_id,
                        Cell: this.scoreCell
                    });
                }
            });
        });

        return {
            columns: columns,
            reviewDetails: reviewDetails,
        };
    }

    loadReviewDetails = () => {
        reviewService
            .getReviewDetails(this.props.event ? this.props.event.id : 0)
            .then(response => {
                if (response.error) {
                    this.setState({
                        isLoading: false,
                        error: response.error
                    });
                    return;
                }
                const result = this.processReviewDetails(response.reviewDetails);
                const sortedReviewDetails = result.reviewDetails.sort((a, b) => a.response_id - b.response_id);
                this.setState({
                    isLoading: false,
                    reviewDetails: sortedReviewDetails,
                    infoColumns: result.columns,
                    error: response.error,
                });
            });
    };

    render() {
        const {
            error,
            isLoading,
            infoColumns,
            reviewDetails,
        } = this.state;

        if (error) {
            return <div className={"alert alert-danger alert-container"}>
                {error}
            </div>;
        }

        const t = this.props.t;

        const columns = [
          {
              Header:  this.props.t("Response ID"),
              accessor: "response_id",
              filterable: false,
              Cell: this.responseIDCell
          },
          {
                id: "reviewer",
                Header:  this.props.t("Reviewer"),
                accessor: r => `${r.reviewer_user_title} ${r.reviewer_user_firstname} ${r.reviewer_user_lastname}`,
                filterable: false,
            },
            {
                Header: this.props.t("Candidate"),
                id: "candidate",
                accessor: r => `${r.response_user_title  } ${r.response_user_firstname} ${r.response_user_lastname}`,
                filterable: false,
            }
        ];

        if (infoColumns) {
            columns.push(...infoColumns)
        }

        columns.push({
            id: "total",
            Header: this.props.t("Total"),
            accessor: "total",
        });

        return (
            <div className="review-list-container">
              <h2 className="title">{t("Review Details")}</h2>
              <div className={"review-padding"}>
                <ReactTable
                  loading={isLoading}
                  manual
                  data={reviewDetails}
                  columns={columns}
                  minRows={0} />
              </div>
            </div>
          );
    }
}

export default withRouter(withTranslation()(ReviewDetailsPage));
