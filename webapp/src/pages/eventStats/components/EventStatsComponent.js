import React, { Component } from "react";
import { Chart } from "react-google-charts";
import { eventStatsService } from "../../../services/eventStats";
import { withRouter } from "react-router";
import { withTranslation } from 'react-i18next';

class EventStatsComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      loading: true,
      buttonLoading: false,
      stats: null,
      error: "",
    };
  }

  componentDidMount() {
    eventStatsService.getStats(
      this.props.event ?
        this.props.event.id : 0).then(result => {
          this.setState({
            loading: false,
            buttonLoading: false,
            stats: result.stats,
            error: result.error
          });
        });
  }

  getStatus = (isOpen, isOpening) => {
    if (isOpen) {
      return <span class="badge badge-pill badge-success">{this.props.t("Open")}</span>
    }
    if (isOpening) {
      return <span class="badge badge-pill badge-secondary">{this.props.t("Not Open")}</span>
    }
    return <span class="badge badge-pill badge-warning">{this.props.t("Closed")}</span>
  }

  plotTimeSeries = (name, timeseries) => {
    if (!timeseries || timeseries.length === 0) {
      return <div></div>
    }

    return <div className="chart">
      <Chart
        chartType="ColumnChart"
        width="100%"
        data={[["Date", name], ...timeseries]}
        options={
          {
            legend: { position: "none" }
          }
        }
        loader={
          <div className="spinner-border" role="status">
            <span class="sr-only">Loading Chart</span>
          </div>}
      />
    </div>
  }

  render() {
    const {
      loading,
      stats,
      error
    } = this.state;

    const loadingStyle = {
      "width": "3rem",
      "height": "3rem"
    }

    if (loading) {
      return (
        <div class="d-flex justify-content-center">
          <div class="spinner-border"
            style={loadingStyle} role="status">
            <span class="sr-only">Loading...</span>
          </div>
        </div>
      )
    }

    if (error) {
      return <div class="alert alert-danger alert-container">
        {error}
      </div>
    }

    const t = this.props.t;

    return (
      <div className={"event-stats text-center"}>
        <div className="row">
          <div className="col-md">
            <div className="stats-title">{t("Applications")}
              {this.getStatus(this.props.event.is_application_open, this.props.event.is_application_opening)}
            </div>

            <div className={"card" + (this.props.event.is_application_opening ? " stats-not-open" : "")}>
              <h1>{stats.num_submitted_responses}</h1>
              <div className="stats-description">{t("Submitted")}</div>
              <br />
              <div className="row">
                <div className="col-sm">
                  <h3>{stats.num_responses - stats.num_submitted_responses - stats.num_withdrawn_responses}</h3>
                  <div className="stats-description">{t("Un-submitted")}</div>
                </div>
                <div className="col-sm">
                  <h3>{stats.num_withdrawn_responses}</h3>
                  <div className="stats-description">{t("Withdrawn")}</div>
                </div>
              </div>
              {this.plotTimeSeries(t("Submitted"), stats.submitted_timeseries)}
            </div>
          </div>
          <div className="col-md">
            <div className="stats-title">{t("Reviews")}
              {this.getStatus(this.props.event.is_review_open, this.props.event.is_review_opening)}
            </div>
            <div className={"card" + (this.props.event.is_review_opening ? " stats-not-open" : "")}>
              <h1>{stats.reviews_completed}</h1>
              <div className="stats-description">{t("Completed")}</div>
              <br />
              <div className="row">
                <div className="col-sm">
                  <h3>{stats.review_incomplete}</h3>
                  <div className="stats-description">{t("Incomplete")}</div>
                </div>
                <div className="col-sm">
                  <h3>{stats.reviews_unallocated}</h3>
                  <div className="stats-description">{t("Not Allocated")}</div>
                </div>
              </div>
              {this.plotTimeSeries(t("Completed"), stats.reviews_complete_timeseries)}
            </div>
          </div>
          <div className="col-md">
            <div className="stats-title">{t("Offers")}
              {this.getStatus(this.props.event.is_offer_open, this.props.event.is_offer_opening)}
            </div>
            <div className={"card" + (this.props.event.is_offer_opening ? " stats-not-open" : "")}>
              <h1>{stats.offers_allocated}</h1>
              <div className="stats-description">{t("Offers Allocated")}</div>
              <br />
              <div className="row">
                <div className="col-sm">
                  <h3>{stats.offers_accepted}</h3>
                  <div className="stats-description">{t("Accepted")}</div>
                </div>
                <div className="col-sm">
                  <h3>{stats.offers_rejected}</h3>
                  <div className="stats-description">{t("Rejected")}</div>
                </div>
              </div>
              {this.plotTimeSeries(t("Accepted"), stats.offers_accepted_timeseries)}
            </div>
          </div>
          <div className="col-md">
            <div className="stats-title">{t("Registration")}
              {this.getStatus(this.props.event.is_registration_open, this.props.event.is_registration_opening)}
            </div>
            <div className={"card" + (this.props.event.is_registration_opening ? " stats-not-open" : "")}>
              <h1>{stats.num_registrations}</h1>
              <div className="stats-description">{t("Registrations")}</div>
              <br />
              <div className="row">
                <div className="col-sm">
                  <h3>{stats.num_guests}</h3>
                  <div className="stats-description">{t("Total Guests")}</div>
                </div>
                <div className="col-sm">
                  <h3>{stats.num_registered_guests}</h3>
                  <div className="stats-description">{t("Registered Guests")}</div>
                </div>
              </div>
              {/* {this.plotTimeSeries(t("Accepted"), stats.registration_timeseries)} */}
            </div>
          </div>
        </div>
      </div>
    )
  }
}

export default withRouter(withTranslation()(EventStatsComponent));