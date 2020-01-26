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
      emailSendStatus: ""
    };
  }

  componentDidMount() {
    eventStatsService.getStats(this.props.event.id).then(result=>{
      this.setState({
        loading: false,
        buttonLoading: false,
        stats: result.stats,
        error: result.error,
        emailSendStatus: ""
      });
    });
  }

  handleSubmit = event => {
    event.preventDefault();
    this.setState({ buttonLoading: true });

    eventStatsService.sendReminderToSubmit(this.props.event.id).then(
      result => {
        return eventStatsService.sendReminderToBegin(this.props.event.id)
      },
      error => this.setState({ error, buttonLoading: false })
    ).then(
      result => {
        this.setState({buttonLoading: false, emailSendStatus: "Reminders sent!"})
      },
      error => this.setState({ error, buttonLoading: false })
    );
  }

  render() {
      const {loading, buttonLoading, emailSendStatus, stats, error} = this.state;

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
            <form onSubmit={this.handleSubmit}>
              <div class="text-center">
                <button type="submit" class="event-action btn btn-primary" visible={!emailSendStatus} >
                  {buttonLoading && (

                    <span
                      class="spinner-grow spinner-grow-sm"
                      role="status"
                      aria-hidden="true"
                    />
                  )}
                  Send Reminders to Applicants
                </button>
                {emailSendStatus && <div className={"alert alert-success"}>{emailSendStatus}</div>}
              </div>
            </form>
          </div>
      )

  }

}

export default withRouter(EventStatsComponent);