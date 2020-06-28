import React, { Component } from "react";
import { Chart } from "react-google-charts";
import { eventStatsService } from "../../../services/eventStats";
import { withRouter } from "react-router";

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
      return <span class="badge badge-pill badge-success">Open</span>
    }
    if (isOpening) {
      return <span class="badge badge-pill badge-secondary">Not Open</span>
    }
    return <span class="badge badge-pill badge-warning">Closed</span>
  }

  plotTimeSeries = (name, timeseries) => {
    if (!timeseries) {
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

    return (
      <div className={"event-stats text-center"}>
        <div className="row">
          <div className="col-md">
            <div className="stats-title">Applications
              {this.getStatus(this.props.event.is_applications_open, this.props.event.is_applications_opening)}
            </div>

            <div className="card">
              {/* TODO: Add dates so we can distinguish between closed and not open yet */}

              <h1>{stats.num_submitted_responses}</h1>
              <div className="stats-description">Submitted</div>
              <br />
              <div className="row">
                <div className="col-sm">
                  <h3>{stats.num_responses - stats.num_submitted_responses - stats.num_withdrawn_responses}</h3>
                  <div className="stats-description">Un-submitted</div>
                </div>
                <div className="col-sm">
                  <h3>{stats.num_withdrawn_responses}</h3>
                  <div className="stats-description">Withdrawn</div>
                </div>
              </div>
              {this.plotTimeSeries("Submitted", stats.submitted_timeseries)}
            </div>
          </div>
          <div className="col-md">
            <div className="stats-title">Reviews
              {this.getStatus(this.props.event.is_review_open, this.props.event.is_review_opening)}
            </div>
            <div className="card">
              <span class="coming-soon">
                Stats Coming Soon
              </span>
            </div>
          </div>
          <div className="col-md">
            <div className="stats-title">Offers
              {this.getStatus(this.props.event.is_offer_open, this.props.event.is_offer_opening)}
            </div>
            <div className="card">
              <span class="coming-soon">
                Stats Coming Soon
              </span>
            </div>
          </div>
          <div className="col-md">
            <div className="stats-title">Registration
              {this.getStatus(this.props.event.is_registration_open, this.props.event.is_registration_opening)}
            </div>
            <div className="card">
              <span class="coming-soon">
                Stats Coming Soon
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }
}

export default withRouter(EventStatsComponent);