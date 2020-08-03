import React, { Component } from "react";
import { withRouter } from "react-router";
import { withTranslation } from 'react-i18next';


class EventStatus extends Component {

  unknownStatus = (status_name, status) => {
      return {
        title: "ERROR",
        titleClass: "text-danger",
        longText: `Unknown ${status_name}: ${status}`,
        shortText: "ERROR"
      }
  }

  registeredStatus = (event) => {
    if (event.status.registration_status === "Confirmed") {
        return {
            title: this.props.t("Registered"),
            titleClass: "text-success",
            longText: this.props.t("You have successfully registered for") + " " + event.name + ", " + this.props.t("we look forward to seeing you soon!"),
            shortText: this.props.t("Registered")
        };
    }
    else if (event.status.registration_status === "Not Confirmed") {
        return {
            title: this.props.t("Pending Confirmation"),
            titleClass: "text-warning",
            longText: this.props.t("Your registration is pending payment confirmation"),
            shortText: this.props.t("Registration Pending")
        };
    }
    else {
        return this.unknownStatus("registration status", event.status.registration_status);
    }
  }

  invitedGuestStatus = (event) => {
    if (!event.status.registration_status) {
        if (event.is_registration_open) {
            return {
                title: this.props.t("Invited Guest"),
                titleClass: "text-success",
                longText: this.props.t("You have been invited as a") + ` ${event.status.invited_guest}, ` + this.props.t("please proceed to registration."),
                shortText: this.props.t("Register"),
                linkClass: 'btn-success',
                link: `${event.key}/registration`
            };
        }
        else {
            return {
                title: this.props.t("Registration Closed"),
                titleClass: "text-danger",
                longText: this.props.t(`Registration is now closed.`),
                shortText: this.props.t("Registration Closed")
            };
        }
    }
    else {
        return this.registeredStatus(event);   
    }
  }

  applicationStatus = (event) => {
      const applyLink = `${event.key}/apply`
      if (event.status.application_status === "Submitted") {
          return {
              title: this.props.t("Application Submitted"),
              titleClass: "text-success",
              longText: this.props.t("You have submitted your application, you may still edit it before the deadline."),
              shortText: this.props.t("View Application"),
              linkClass: 'btn-secondary',
              link: applyLink
          };
      }
      else if (event.status.application_status === "Withdrawn") {
        return {
            title: this.props.t("Application Withdrawn"),
            titleClass: "text-danger",
            longText: this.props.t("Your application has been withdrawn, you will not be considered for") + ` ${event.name} ` + this.props.t("unless you re-submit by the deadline."),
            shortText: this.props.t("Re-apply"),
            linkClass: "btn-warning",
            link: applyLink
        };
      }
      else if (event.status.application_status === "Not Submitted") {
          return {
              title: this.props.t("In Progress"),
              titleClass: "text-warning",
              longText: this.props.t(`You have not yet submitted your application, you must do so before the deadline to be considered`),
              shortText: this.props.t("Continue"),
              linkClass: "btn-primary",
              link: applyLink
          };
      }
      else {
          return {
              title: this.props.t("Apply Now"),
              titleClass: "text-success",
              longText: this.props.t("Start your application to attend") + ` ${event.name}`,
              shortText: this.props.t("Apply Now"),
              linkClass: "btn-success",
              link: applyLink
          };
      }
  }

  offerStatus = (event) => {
    if (event.status.offer_status === "Accepted") {
        if (event.status.registration_status) {
            return this.registeredStatus(event);
        }
        else if (event.is_registration_open) {
            return {
                title: this.props.t("Register Now"),
                titleClass: "text-success",
                longText: this.props.t("You have accepted your offer to attend") + ` ${event.name}. Please complete your event registration as soon as possible.`,
                shortText: this.props.t("Register Now"),
                linkClass: "btn-success",
                link: `${event.key}/registration`
            };
        }
        else {
            return {
                title: this.props.t("Registration Closed"),
                titleClass: "text-danger",
                longText: this.props.t(`Registration is now closed.`),
                shortText: this.props.t("Registration Closed)")
            };
        }
    }
    else if (event.status.offer_status === "Rejected") {
        return {
            title: this.props.t("Offer Rejected"),
            titleClass: "text-danger",
            longText: this.props.t("You have turned down your offer to attend") + ` ${event.name}.` + this.props.t("We hope to see you at a future event!"),
            shortText: this.props.t("Offer Rejected")
        };
    }
    else if (event.status.offer_status === "Expired") {
        return {
            title: this.props.t("Offer Expired"),
            titleClass: "text-danger",
            longText: this.props.t("Unfortunately your offer attend") + ` ${event.name} ` + this.props.t("has expired."),
            shortText: this.props.t("Offer Expired")
        };
    }
    else if (event.status.offer_status === "Pending") {
        return {
            title: this.props.t("Application Successful"),
            titleClass: "text-success",
            longText: this.props.t("Congratulations! You have a pending offer to attend") + ` ${event.name}. ` + this.props.t("Please accept or reject it before the expiry date."),
            shortText: this.props.t("View Offer"),
            linkClass: "btn-success",
            link: `${event.key}/offer`
        };
    }
    else {
        return this.unknownStatus("offer status", event.status.offer_status);
    }
  }

  outcomeStatus = (event) => {
      if (event.status.outcome_status === "ACCEPTED") {
          return {
            title: this.props.t("Application Successful"),
            titleClass: "text-success",
            longText: this.props.t("Congratulations! You have been accepted to attend") + ` ${event.name}. ` + this.props.t("Further details will follow shortly!"),
            shortText: this.props.t("Application Successful")
          };
      }
      else if (event.status.outcome_status === "REJECTED") {
          return {
              title: this.props.t("Application Unsuccessful"),
              titleClass: "text-danger",
              longText: this.props.t("Unfortunately your application to attend") + ` ${event.name} ` + this.props.t("was not successful. Please try again next time!"),
              shortText: this.props.t("Application Unsuccessful")
          };
      }
      else if (event.status.outcome_status === "WAITLIST") {
        return {
            title: this.props.t("Waitlist"),
            titleClass: "text-warning",
            longText: this.props.t("You are on the waiting list for") + ` ${event.name}. ` + this.props.t("Please keep an eye out for further communication."),
            shortText: this.props.t("Waitlist")
        };
      }
      else {
          return this.unknownStatus("outcome status", event.status.outcome_status);
      }
  }

  applicationClosedStatus = (event) => {
      if (event.status.application_status === "Submitted") {
          return {
              title: this.props.t("Application Submitted"),
              titleClass: "text-success",
              longText: this.props.t("Your application is being reviewed. We will get back to you with a verdict as soon as possible."),
              shortText: this.props.t("Applied")
          }
      }
      else if (event.status.application_status === "Withdrawn") {
          return {
              title: this.props.t("Application Withdrawn"),
              titleClass: "text-danger",
              longText: this.props.t("You withdrew your application to") + ` ${event.name} ` + this.props.t("and applications are now closed. Your application will therefore not be considered"),
              shortText: this.props.t("Application Withdrawn")
          }
      }
      else if (event.status.application_status === "Not Submitted") {
          return {
              title: this.props.t("Applications Closed"),
              titleClass: "text-danger",
              longText: this.props.t("You started, but did not submit your application before the deadline. Your application will therefore not be considered"),
              shortText: this.props.t("Applications Closed")
          }
      }
      else {
          return {
              title: this.props.t("Applications Closed"),
              titleClass: "text-danger",
              longText: this.props.t("You did not apply to") + ` ${event.name} ` + this.props.t("and applications are now closed."),
              shortText: this.props.t("Applications Closed")
          }
      }
  }

  eventStatus = (event) => {
      if (event.miniconf_url) {
        const link = 
            "https://" +
            event.miniconf_url +
            "/index.html?token=" +
            JSON.parse(localStorage.getItem("user"))["token"] +
            "&event_id=" + 
            event.id +
            "&redirect_back_url=" +
            window.location.href +
            "&verify_token_url=" +
            process.env.REACT_APP_API_URL +
            "/api/v1/validate-user-event-attendee" +
            "&origin=" +
            window.location.origin;

        return {
            title: this.props.t("Virtual Event Now Open"),
            titleClass: "text-success",
            longText: `${event.name} ` + this.props.t("is now open! Please visit our virtual event site to attend."),
            shortText: this.props.t('Go To Virtual Event >'),
            linkClass: "btn-success",
            link: link
        }
      }
      else {
          return {
              title: this.props.t("Enjoy the Event"),
              titleClass: "text-success",
              shortText: this.props.t("Now Live")
          }
      }
      
  }

  eventComingSoonStatus = (event) => {
    if (event.miniconf_url) {
        return {
            title: this.props.t("Virtual Event Opening Soon!"),
            titleClass: "text-success",
            longText: `${event.name} ` + this.props.t("is opening soon - our virtual event site will be live on") + ` ${event.start_date}.`,
            shortText: this.props.t("Virtual Event Opens") + ` ${event.start_date}`,
        }
    }
    else {
        return {
            title: this.props.t("Enjoy the Event"),
            titleClass: "text-success",
            shortText: `Starts ${event.start_date}!`
        }
    }
  }

  mapStatus = (event) => {
      if (event.status === null) {
        return this.unknownStatus("Status", this.props.t("Please try refresh the page and/or clear your cookies"));
      }

      if (!event.is_registration_open && event.is_event_opening && event.status.is_event_attendee) {
          return this.eventComingSoonStatus(event);
      }

      if (event.is_event_open && event.status.is_event_attendee) {
          return this.eventStatus(event);
      }

      if (event.status.invited_guest) {
        return this.invitedGuestStatus(event);
      }
      
      if (event.is_application_open) {
          return this.applicationStatus(event);
      }

      if (event.status.offer_status) {
          return this.offerStatus(event);
      }

      if (event.status.outcome_status) {
          return this.outcomeStatus(event);
      }

      return this.applicationClosedStatus(event);

  }

  renderButton = (definition) => {
    return <a href={definition.link} className={"btn " + definition.linkClass}>{definition.shortText}</a> 
  }

  render() {
    const definition = this.mapStatus(this.props.event);
    if (this.props.longForm) {
        return <div>
            <h3 className={definition.titleClass}>{definition.title}</h3>
            <p>{definition.longText}</p><br/>
            {definition.shortText && definition.link && this.renderButton(definition)}
        </div>
    }
    else {
        if (definition.shortText && definition.link && definition.title !== definition.shortText) {
            return <div>
                <span>{definition.title}</span><br/>{this.renderButton(definition)}
            </div>
        }
        else if (definition.shortText && definition.link) {
            return this.renderButton(definition);
        }
        else {
            return <span>{definition.shortText}</span>
        }
    }
  }
}

export default withRouter(withTranslation()(EventStatus));
