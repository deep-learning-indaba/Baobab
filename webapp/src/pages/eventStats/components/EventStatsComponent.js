import React, { Component } from "react";
import { Chart } from "react-google-charts";
import { eventStatsService } from "../../../services/eventStats";
import { withRouter } from "react-router";

const DEFAULT_EVENT_ID = process.env.DEFAULT_EVENT_ID || 1;

class EventStatsComponent extends Component {
  constructor(props) {
    super(props);

    this.state = {
      loading: true,
      stats: null,
      error: ""
    };
  }

  componentDidMount() {
    eventStatsService.getStats(DEFAULT_EVENT_ID).then(result=>{
      this.setState({
        loading: false,
        stats: result.stats,
        error: result.error
      });
    });
  }

  render() {
      const {loading, stats, error} = this.state;

      const loadingStyle = {
        "width": "3rem",
        "height": "3rem"
      }

      if (loading) {
        return (
          <div class="d-flex justify-content-center">
            <div class="spinner-border" style={loadingStyle} role="status">
              <span class="sr-only">Loading...</span>
            </div>
          </div>
        )
      }

      if (error) {
        return <div class="alert alert-danger">{error}</div>
      }
      
      const submitted = stats.num_submitted_responses;
      const not_submitted = stats.num_responses - submitted;
      const not_started = stats.num_users - stats.num_responses;

      return (
        <div className={"event-stats text-center"}>
          <p className="h5">Statistics for {stats.event_description}</p>
          <Chart 
            chartType="PieChart" 
            loader={<div class="spinner-border" role="status"><span class="sr-only">Loading Chart</span></div>}
            data={[
              ['Phase', 'Number'],
              ['Not Started', not_started],
              ['Not Submitted', not_submitted],
              ['Complete', submitted],
            ]}
            options={{
              title: 'Number of applications',
            }}
          />
        </div>
      )
  }

}

export default withRouter(EventStatsComponent);