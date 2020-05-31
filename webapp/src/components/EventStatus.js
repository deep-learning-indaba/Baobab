import React, { Component } from "react";
import { withRouter } from "react-router";


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
    if (event.stats.registration_status === "Confirmed") {
        return {
            title: "Registered",
            titleClass: "text-success",
            longText: `You have successfully registered for ${event.name}, we look forward to seeing you soon!`,
            shortText: "Registered"
        };
    }
    else if (event.status.registration_status === "Not Confirmed") {
        return {
            title: "Pending Confirmation",
            titleClass: "text-warning",
            longText: "Your registration is pending payment confirmation",
            shortText: "Registration Pending"
        };
    }
    else {
        return this.unknownStatus("registration status", event.status.registration_status);
    }
  }

  invitedGuestStatus = (event) => {
    if (!event.status.registration_status) {
        return {
            title: "Invited Guest",
            titleClass: "text-success",
            longText: `You have been invited as a ${event.status.invited_guest}, please proceed to registration.`,
            shortText: "Register",
            linkClass: 'btn-success',
            link: `${event.key}/registration`
        };
    }
    else {
        return this.registeredStatus();   
    }
  }

  applicationStatus = (event) => {
      const applyLink = `${event.key}/apply`
      if (event.status.application_status === "Submitted") {
          return {
              title: "Application Submitted",
              titleClass: "text-success",
              longText: "You have submitted your application, you may still edit it before the deadline.",
              shortText: "View Application",
              linkClass: 'btn-secondary',
              link: applyLink
          };
      }
      else if (event.status.application_status === "Withdrawn") {
        return {
            title: "Application Withdrawn",
            titleClass: "text-danger",
            longText: `Your application has been withdrawn, you will not be considered for a place at ${event.name} unless you re-submit by the deadline.`,
            shortText: "Re-apply",
            linkClass: "btn-warning",
            link: applyLink
        };
      }
      else if (event.status.application_status === "Not Submitted") {
          return {
              title: "In Progress",
              titleClass: "text-warning",
              longText: `You have not yet submitted your application, you must do so before the deadline to be considered`,
              shortText: "Continue",
              linkClass: "btn-primary",
              link: applyLink
          };
      }
      else {
          return {
              title: "Apply Now",
              titleClass: "text-success",
              longText: `Start your application to attend ${event.name}`,
              shortText: "Apply Now",
              linkClass: "btn-success",
              link: applyLink
          };
      }
  }

  offerStatus = (event) => {
    if (event.status.offer_status === "Accepted") {
        if (event.status.registration_status) {
            return this.registeredStatus();
        }
        else {
            return {
                title: "Register Now",
                titleClass: "text-success",
                longText: `You have accepted your offer to attend ${event.name}. Please complete your event registration as soon as possible.`,
                shortText: "Register Now",
                linkClass: "btn-success",
                link: `${event.key}/registration`
            };
        }
    }
    else if (event.status.offer_status === "Rejected") {
        return {
            title: "Offer Rejected",
            titleClass: "text-danger",
            longText: `You have turned down your offer to attend ${event.name}. We hope to see you at a future event!`,
            shortText: "Offer Rejected"
        };
    }
    else if (event.status.offer_status === "Expired") {
        return {
            title: "Offer Expired",
            titleClass: "text-danger",
            longText: `Unfortunately your offer attend ${event.name} as expired.`,
            shortText: "Offer Expired"
        };
    }
    else if (event.status.offer_status === "Pending") {
        return {
            title: "Application Successful",
            titleClass: "text-success",
            longText: `Congratulations! You have a pending offer to attend ${event.name}. Please accept or reject it before the expiry date.`,
            shortText: "View Offer",
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
            title: "Application Successful",
            titleClass: "text-success",
            longText: `Congratulations! You have been accepted to attend ${event.name}. Further details will follow shortly!`,
            shortText: "Application Successful"
          };
      }
      else if (event.status.outcome_status === "REJECTED") {
          return {
              title: "Application Unsuccessful",
              titleClass: "text-danger",
              longText: `Unfortunately your application to attend ${event.name} was not successful. Please try again next time!`,
              shortText: "Application unsuccessful"
          };
      }
      else if (event.status.outcome_status === "WAITLIST") {
        return {
            title: "Waitlist",
            titleClass: "text-warning",
            longText: `You are on the waiting list for ${event.name}. Please keep an eye out for further communication.`,
            shortText: "Waitlist"
        };
      }
      else {
          return this.unknownStatus("outcome status", event.status.outcome_status);
      }
  }

  applicationClosedStatus = (event) => {
      if (event.status.application_status === "Submitted") {
          return {
              title: "Application Submitted",
              titleClass: "text-success",
              longText: "Your application is being reviewed. We will get back to you with a verdict as soon as possible.",
              shortText: "Applied"
          }
      }
      else if (event.status.application_status === "Withdrawn") {
          return {
              title: "Application Withdrawn",
              titleClass: "text-danger",
              longText: `You withdrew your application to attend ${event.name} and applications are now closed. You will not be considered for a place at the event.`,
              shortText: "Application Withdrawn"
          }
      }
      else if (event.status.application_status === "Not Submitted") {
          return {
              title: "Applications Closed",
              titleClass: "text-danger",
              longText: `You started, but did not submit your application before the deadline. You will therefore not be considered for a place at ${event.name}`,
              shortText: "Applications Closed"
          }
      }
      else {
          return {
              title: "Applications Closed",
              titleClass: "text-danger",
              longText: `You did not apply to attend ${event.name} and applications are now closed.`,
              shortText: "Applications Closed"
          }
      }
  }

  mapStatus = (event) => {
      if (event.status === null) {
        return self.unknownStatus("Status", "Please try refresh the page and/or clear your cookies");
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

export default withRouter(EventStatus);
