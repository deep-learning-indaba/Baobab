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
      return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800 tracking-wide">{this.props.t("Open")}</span>
    }
    if (isOpening) {
      return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-surface-high text-muted-foreground tracking-wide">{this.props.t("Not Open")}</span>
    }
    return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 tracking-wide">{this.props.t("Closed")}</span>
  }

  plotTimeSeries = (name, timeseries) => {
    if (!timeseries || timeseries.length === 0) {
      return <div></div>
    }

    return <div className="mt-4 w-full h-[100px] overflow-hidden -mx-2">
      <Chart
        chartType="ColumnChart"
        width="100%"
        height="100px"
        data={[["Date", name], ...timeseries]}
        options={
          {
            legend: { position: "none" },
            colors: ['#0f5238'],
            backgroundColor: 'transparent',
            chartArea: { left: 0, top: 0, width: '100%', height: '100%' },
            hAxis: { textPosition: 'none', gridlines: { color: 'transparent' }, baselineColor: 'transparent' },
            vAxis: { textPosition: 'none', gridlines: { color: 'transparent' }, baselineColor: 'transparent' }
          }
        }
        loader={
          <div className="flex justify-center items-center h-full text-primary">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
          </div>}
      />
    </div>
  }

  render() {
    const { loading, stats, error } = this.state;
    const t = this.props.t;

    if (loading) {
      return (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      )
    }

    if (error) {
      return <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm mb-6 mt-4">
        {error}
      </div>
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        
        {/* Applications Stats */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 px-1">
            <h3 className="font-semibold text-foreground text-sm tracking-wider">{t("Applications")}</h3>
            {this.getStatus(this.props.event.is_application_open, this.props.event.is_application_opening)}
          </div>
          <div className={"bg-white rounded-2xl shadow-sm border border-border p-6 flex flex-col items-center text-center transition-opacity" + (this.props.event.is_application_opening ? " opacity-60" : "")}>
            <div className="text-4xl font-heading font-bold text-primary mb-1">{stats.num_submitted_responses}</div>
            <div className="text-sm font-semibold text-muted-foreground tracking-wider mb-6">{t("Submitted")}</div>
            
            <div className="flex w-full justify-between gap-4 border-t border-border/50 pt-4">
              <div className="flex-1">
                <div className="text-xl font-bold text-foreground">{stats.num_responses - stats.num_submitted_responses - stats.num_withdrawn_responses}</div>
                <div className="text-xs font-semibold text-muted-foreground tracking-wider mt-1">{t("Un-submitted")}</div>
              </div>
              <div className="flex-1">
                <div className="text-xl font-bold text-foreground">{stats.num_withdrawn_responses}</div>
                <div className="text-xs font-semibold text-muted-foreground tracking-wider mt-1">{t("Withdrawn")}</div>
              </div>
            </div>
            {this.plotTimeSeries(t("Submitted"), stats.submitted_timeseries)}
          </div>
        </div>

        {/* Reviews Stats */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 px-1">
            <h3 className="font-semibold text-foreground text-sm tracking-wider">{t("Reviews")}</h3>
            {this.getStatus(this.props.event.is_review_open, this.props.event.is_review_opening)}
          </div>
          <div className={"bg-white rounded-2xl shadow-sm border border-border p-6 flex flex-col items-center text-center transition-opacity" + (this.props.event.is_review_opening ? " opacity-60" : "")}>
            <div className="text-4xl font-heading font-bold text-primary mb-1">{stats.reviews_completed}</div>
            <div className="text-sm font-semibold text-muted-foreground tracking-wider mb-6">{t("Completed")}</div>
            
            <div className="flex w-full justify-between gap-4 border-t border-border/50 pt-4">
              <div className="flex-1">
                <div className="text-xl font-bold text-foreground">{stats.review_incomplete}</div>
                <div className="text-xs font-semibold text-muted-foreground tracking-wider mt-1">{t("Incomplete")}</div>
              </div>
              <div className="flex-1">
                <div className="text-xl font-bold text-foreground">{stats.reviews_unallocated}</div>
                <div className="text-xs font-semibold text-muted-foreground tracking-wider mt-1">{t("Not Allocated")}</div>
              </div>
            </div>
            {this.plotTimeSeries(t("Completed"), stats.reviews_complete_timeseries)}
          </div>
        </div>

        {/* Offers Stats */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 px-1">
            <h3 className="font-semibold text-foreground text-sm tracking-wider">{t("Offers")}</h3>
            {this.getStatus(this.props.event.is_offer_open, this.props.event.is_offer_opening)}
          </div>
          <div className={"bg-white rounded-2xl shadow-sm border border-border p-6 flex flex-col items-center text-center transition-opacity" + (this.props.event.is_offer_opening ? " opacity-60" : "")}>
            <div className="text-4xl font-heading font-bold text-primary mb-1">{stats.offers_allocated}</div>
            <div className="text-sm font-semibold text-muted-foreground tracking-wider mb-6">{t("Allocated")}</div>
            
            <div className="flex w-full justify-between gap-2 border-t border-border/50 pt-4">
              <div className="flex-1">
                <div className="text-lg font-bold text-green-600">{stats.offers_accepted}</div>
                <div className="text-xs font-semibold text-muted-foreground tracking-wider mt-1">{t("Accepted")}</div>
              </div>
              <div className="flex-1">
                <div className="text-lg font-bold text-action">{stats.offers_confirmed}</div>
                <div className="text-xs font-semibold text-muted-foreground tracking-wider mt-1">{t("Confirmed")}</div>
              </div>
              <div className="flex-1">
                <div className="text-lg font-bold text-error">{stats.offers_rejected}</div>
                <div className="text-xs font-semibold text-muted-foreground tracking-wider mt-1">{t("Rejected")}</div>
              </div>
            </div>
            {this.plotTimeSeries(t("Accepted"), stats.offers_accepted_timeseries)}
          </div>
        </div>

        {/* Registration Stats */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 px-1">
            <h3 className="font-semibold text-foreground text-sm tracking-wider">{t("Registration")}</h3>
            {this.getStatus(this.props.event.is_registration_open, this.props.event.is_registration_opening)}
          </div>
          <div className={"bg-white rounded-2xl shadow-sm border border-border p-6 flex flex-col items-center text-center transition-opacity h-full" + (this.props.event.is_registration_opening ? " opacity-60" : "")}>
            <div className="text-4xl font-heading font-bold text-primary mb-1">{stats.num_registrations}</div>
            <div className="text-sm font-semibold text-muted-foreground tracking-wider mb-6">{t("Registrations")}</div>
            
            <div className="flex w-full justify-between gap-4 border-t border-border/50 pt-4 mt-auto">
              <div className="flex-1">
                <div className="text-xl font-bold text-foreground">{stats.num_guests}</div>
                <div className="text-xs font-semibold text-muted-foreground tracking-wider mt-1">{t("Total Guests")}</div>
              </div>
              <div className="flex-1">
                <div className="text-xl font-bold text-foreground">{stats.num_registered_guests}</div>
                <div className="text-xs font-semibold text-muted-foreground tracking-wider mt-1">{t("Registered Guests")}</div>
              </div>
            </div>
          </div>
        </div>

      </div>
    )
  }
}

export default withRouter(withTranslation()(EventStatsComponent));