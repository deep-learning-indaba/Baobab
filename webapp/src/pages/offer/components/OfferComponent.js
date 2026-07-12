import React, { Component } from "react";
import { withRouter } from "react-router";
import { offerServices } from "../../../services/offer/offer.service";
import { applicationFormService } from "../../../services/applicationForm/applicationForm.service.js"
import { userService } from "../../../services/user/user.service";
import { NavLink } from "react-router-dom";
import { Trans, withTranslation } from 'react-i18next';
import { getDownloadURL } from "../../../utils/files";

class Offer extends Component {
  constructor(props) {
    super(props);

    this.state = {
      user: {},
      userProfile: {},
      loading: true,
      saving: false,
      error: "",
      rejected_reason: "",
      showReasonBox: false,
      candidate_response: null,
      offer: null,
      noOffer: null,
      category: "",
      grant_tags: [],
      note_tags: [],
      applicationExist: null
    };
  }

  resetPage = () => {
    this.componentWillMount()
  }

  handleChange = field => {
    return event => {
      this.setState({
        rejected_reason: event.target.value
      });
    };
  };

  buttonSubmit = (candidate_response) => {
    const { offer,
      rejected_reason,
      grant_tags,
    } = this.state;

    this.setState({saving: true});

    if (candidate_response !== null) {
      offerServices
        .updateOffer(
          offer.id,
          this.props.event ? this.props.event.id : 0,
          candidate_response,
          candidate_response ? "" : rejected_reason,
          grant_tags.map(t => {
            return { 'id': t.id, 'accepted': t.accepted }}
            ))
        .then(response => {
          if (response.response && response.response.status === 201) {
            this.setState({
              offer: response.response.data,
              grant_tags: this.initGrants(response.response.data.tags),
              note_tags: this.initNotes(response.response.data.tags),
              showReasonBox: false,
              saving: false
            }, () => {
              if (candidate_response && this.state.offer.is_confirmed && this.props.event) {
                this.props.history.push(`/${this.props.event.key}/registration`);
              }
            });
          } else if (response.error) {
            this.setState({
              error: response.error,
              showReasonBox: false
            });
          }
        });
    }
  }

  row = (col1, col2) => {
    return <div className="flex w-full py-3 border-b border-border/50 last:border-0">
      <div className="w-1/3 font-semibold text-muted-foreground pr-4 text-right">{col1}:</div>
      <div className="w-2/3 pl-4 text-foreground text-left">{col2}</div>
    </div>
  }

  onChangeGrant = tag_id => {
    const u = this.state.grant_tags;
    u.forEach(t => {
      if (t.id === tag_id) {
        t.accepted = !t.accepted;
      }
    });
    this.setState({
      grant_tags: u
    });
  }

  displayOfferResponse = () => {
    const { offer, grant_tags, saving } = this.state;
    const event = this.props.event;
    const t = this.props.t;

    const eventName = event ? event.name : "";
    const respondedDate = offer.responded_at ? offer.responded_at.substring(0, 10) : "-date-";
    const paymentAmount = offer.payment_amount;
    const paymentCurrency = offer.payment_currency;
    const acceptedGrants = grant_tags.filter(a => a.accepted);

    return (
      <div className="w-full max-w-5xl mx-auto space-y-6">
        <p className="text-base text-muted-foreground mb-4">
          {offer.candidate_response && offer.is_confirmed && <span><Trans i18nKey="spotAccepted">You accepted the following offer on {{respondedDate}}</Trans>.</span>}
          {!offer.candidate_response && <span><Trans i18nKey="spotRejected">You rejected your offer for a spot at {{eventName}} on {{respondedDate}} for the following reason:</Trans><br/><br/>{offer.rejected_reason}</span>}
          {offer.candidate_response && !offer.is_confirmed && !offer.is_expired && <span>{t("Your offer is pending receipt of payment")}</span>}
          {offer.candidate_response && !offer.is_confirmed && offer.is_expired && <span className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center block mt-4">{t("Your offer has expired due to non payment")}</span>}
        </p>

        {offer.candidate_response && (offer.is_confirmed || (!offer.is_confirmed && !offer.is_expired)) && <div className="bg-white rounded-2xl shadow-sm border border-border p-6 space-y-2 mt-8">
          {this.row("Offer date", offer.offer_date ? offer.offer_date.substring(0, 10) : "-date-")}
          {this.row("Offer expiry date", offer.expiry_date ? offer.expiry_date.substring(0, 10) : "-date-")}
          {this.row("Registration fee", 
                    offer.payment_required 
                    ? offer.is_paid 
                        ? t("You have paid your registration fee, thank you")
                        : <Trans i18nKey="paymentRequired">Payment of {{paymentAmount}} {{paymentCurrency}} is required to confirm your place</Trans>
                    : t("Fee Waived"))}

          {this.props.event && acceptedGrants.length > 0 && this.row(t("Grants"), t("You have accepted the following grants") + ": " + acceptedGrants.map(a => a.name).join(", "))}
        </div>}

        {offer.candidate_response && offer.is_confirmed &&
          <div className="flex flex-wrap gap-4 mt-6">
            <div className="flex-1 text-center">
              <button
                type="button"
                className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-error text-error-foreground hover:bg-error/90 shadow-sm w-full"
                id="reject"
                disabled={saving}
                onClick={() => {
                  this.setState(
                    {
                      showReasonBox: true
                    });
                }}>
                {t("Reject")}
                </button>
            </div>

            <div className="flex-1 text-center">
              <NavLink className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm w-full text-center" to={`/${this.props.event.key}/registration`}>
                {t("Proceed to Registration")}
              </NavLink>
            </div>
          </div>
        }

        {
          // If the user has accepted the offer but has not paid the registration fee, and the offer is not expired, show the invoice & payment button
          offer.candidate_response && !offer.is_confirmed && !offer.is_expired &&
          <div className="flex flex-wrap gap-4 mt-6">
            <div className="flex-1 text-center">
              <button
                type="button"
                className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-error text-error-foreground hover:bg-error/90 shadow-sm w-full"
                id="reject"
                disabled={saving}
                onClick={() => {
                  this.setState(
                    {
                      showReasonBox: true
                    });
                }}>
                {t("Reject")}
              </button>
            </div>

            <div className="flex-1 text-center">
              <a href={getDownloadURL(`invoice_${offer.invoice_number}.pdf`, "indaba-invoices")} className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-surface-high text-foreground hover:bg-surface-high/80 border border-border w-full">
                {t("View Invoice")}
              </a>
            </div>
            <div className="flex-1 text-center">
              <NavLink className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm w-full text-center" to={`/payment/${offer.invoice_id}`}>
                {t("Pay Online")}
              </NavLink>
            </div>
          </div>
        }

        {this.state.showReasonBox &&
          <div className="flex flex-col gap-4 mt-6">
            <textarea
              className="w-full border border-border rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all min-h-[120px] resize-y"
              onChange={this.handleChange(this.state.rejected_reason)}
              placeholder={t("Please let us know why you are rejecting this offer")} />
            <button
              type="button"
              className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-error/10 text-error hover:bg-error/20 border border-error/20"
              disabled={saving}
              onClick={() => {
                this.setState({
                  candidate_response: false
                },
                  this.buttonSubmit(false)
                );
              }}>
              {t("Submit")}
            </button>
          </div>
        }
      </div>);
  }

  renderNotes = () => {
    const { note_tags } = this.state;
    const t = this.props.t;

    if (!note_tags || note_tags.length === 0) {
      return null;
    }

    return <div className="flex flex-col gap-4 mb-4">
      <div className="w-full font-semibold text-lg text-foreground pr-2 text-left">{t("Notes")}</div>
      <div className="w-full">
        {note_tags.map((note_tag) => {
          return <div className="flex flex-wrap gap-4 mb-2 offer-note" key={"note_tag_" + note_tag.id}>
            <div className="w-full md:w-1/6 px-3">
              <span className="font-bold">{note_tag.name}</span>
            </div>
            <div className="w-full md:w-5/6 px-3 text-foreground/80">
              {note_tag.description}
            </div>
          </div>;
        })}
      </div>
      <div className="w-full border-t border-border/50 my-2"></div>
    </div>;
  }

  renderGrants = () => {
    const { grant_tags } = this.state;
    const t = this.props.t;

    return <div className="flex flex-col gap-4 mb-4">
      <div className="w-full font-semibold text-lg text-foreground pr-2 text-left">{t("Grants")}</div>
      {grant_tags.length > 0 ?
        <div className="space-y-4">
          <div className="w-full pr-2 text-left">
            <div className="mb-4 text-foreground">{t("We are pleased to offer you the following grants") + ":"}</div>
          </div>
          {grant_tags.map((grant_tag) => {
            return <div className="flex flex-wrap gap-4 mb-4 items-center text-left bg-surface-low rounded-xl p-4 border border-border" key={"grant_tag_"+grant_tag.id}>
                      <div className="w-full md:w-1/6 px-2">
                        <span className="font-bold text-primary">{grant_tag.name}</span>
                        
                      </div>
                      <div className="w-full md:w-1/2 px-2 text-sm text-foreground/80">
                        {grant_tag.description}
                      </div>
                      <div className="w-full md:w-1/4 px-2">
                        <div className="flex items-center gap-2">
                          <input type="checkbox" className="rounded border-border text-primary focus:ring-primary w-4 h-4 cursor-pointer"
                            checked={grant_tag.accepted}
                            onChange={() => this.onChangeGrant(grant_tag.id)}
                            id={"check_" + grant_tag.id} />
                          <label className="text-sm font-medium text-foreground cursor-pointer select-none" htmlFor={"check_"+grant_tag.id}>{t("I accept this grant")}</label>
                        </div>
                      </div>
                    </div>
          })}
        </div>
        :
        <div className="w-full text-center text-muted-foreground bg-surface-low p-4 rounded-xl text-sm">{t("Please note that this offer does not include any grants. We appreciate your understanding.")}</div>
      } 
      <div className="w-full border-t border-border/50 my-2"></div>
    </div>
  }

  displayOfferContent = e => {
    const { offer,
      rejected_reason,
      grant_tags,
      saving
    } = this.state;

    const t = this.props.t;
    const paymentAmount = offer.payment_amount;
    const paymentCurrency = offer.payment_currency;

    return (
      <div className="w-full max-w-5xl mx-auto space-y-6">
        {offer.candidate_response !== null ?
          this.displayOfferResponse()
          :
          <div>
            <p className="text-base text-muted-foreground mb-4">
                {t("We are pleased to offer you a place at") + " " + (this.props.event ? this.props.event.name : "") + ". "}
                {t("Please see the details of this offer below") + "."}
            </p>

            <form className="bg-white rounded-2xl shadow-sm border border-border p-6 space-y-6 mt-6">
                <p className="text-xl font-bold font-heading text-foreground mb-4">{t("Offer Details")}</p>

                {this.props.event && grant_tags && this.renderGrants()}
                {this.renderNotes()}

                <div className="flex flex-wrap gap-4 mb-2">
                  <div className="w-full font-semibold text-lg text-foreground pr-2 text-left">{t("Registration Fee")}</div>
                </div>
                <div className="flex flex-wrap gap-4 mb-6">
                  <div className="w-full text-left">
                    {offer && offer.payment_required && <Trans i18nKey="registrationFee">In order to confirm your place, you will be liable for a {{paymentAmount}} {{paymentCurrency}} registration fee.</Trans>}
                    {offer && !offer.payment_required && (t("Your registration fee has been waived") + ".")}
                  </div>
                </div>

                <p className="font-bold text-foreground">
                  {t("Please accept or reject this offer by")}{" "}
                  {offer !== null ? offer.expiry_date !== undefined ? offer.expiry_date.substring(0, 10) : "-date-" : "unable to load expiry date"}{" "}
                </p>

                <div className="mt-4">
                  {this.state.showReasonBox ? (
                    <div className="flex flex-col gap-4 mt-4">
                      <textarea
                        className="w-full border border-border rounded-lg px-4 py-3 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all min-h-[120px] resize-y"
                        onChange={this.handleChange(rejected_reason)}
                        placeholder={t("Enter rejection message")} />
                      <button
                        type="button"
                        className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-error/10 text-error hover:bg-error/20 border border-error/20 w-fit"
                        disabled={saving}
                        onClick={() => {
                          this.setState(
                            {
                              candidate_response: false
                            },
                            this.buttonSubmit(false)
                          );
                        }}>
                        {t("Submit")}
                  </button>
                    </div>
                  ) : (
                      <div className="flex flex-wrap gap-4 mt-6">
                        <div className="flex-1 text-center">
                          <button
                            type="button"
                            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-error text-error-foreground hover:bg-error/90 shadow-sm w-full"
                            id="reject"
                            disabled={saving}
                            onClick={() => {
                              this.setState({
                                showReasonBox: true
                              });
                            }}>
                            {t("Reject")}
                    </button>
                        </div>

                        <div className="flex-1 text-center">
                          <button
                            type="button"
                            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-green-600 text-white hover:bg-green-700 shadow-sm w-full"
                            id="accept"
                            disabled={saving}
                            onClick={() => {
                              this.setState({
                                candidate_response: true
                              }
                              );
                              this.buttonSubmit(true)
                            }}>
                            {t("Accept")}
                    </button>
                        </div>
                      </div>
                    )}

                </div>
            </form>
          </div>
        }
      </div>
    );
  };

  componentWillMount() {
    userService.get().then(results => {
      this.setState({
        userProfile: results,
        error: results.error
      }, this.getOffer);
    });
  }

  componentDidMount() {
    applicationFormService.getResponse(this.props.event ? this.props.event.id : 0)
      .then(results => {
        if (results.response && results.response.length > 0 && results.response[0].is_submitted && !results.response[0].is_withdrawn) {
          this.setState({
            applicationExist: true
          });
        } else {
          this.setState({
            applicationExist: false
          });
        }
      });
  }

  getOffer = () => {
    this.setState({ loading: true });
    offerServices.getOffer(this.props.event ? this.props.event.id : 0)
      .then(result => {
        if (result.error && result.statusCode === 404) {
          this.setState({
            noOffer: true,
            loading: false
          });
        } else if (result.error) {
          this.setState({
            error: result.error,
            loading: false
          });
        } else {
          this.setState({
            loading: false,
            offer: result.offer,
            error: result.error,
            grant_tags: this.initGrants(result.offer.tags),
            note_tags: this.initNotes(result.offer.tags)
          });
        }
      });
  }

  initGrants = (tags) => {
    return tags.filter(tag => tag.tag_type === "GRANT").map(tag => {
      return {
        ...tag,
        accepted: tag.accepted === null ? true : tag.accepted,
        }
      });
  }

  initNotes = (tags) => {
    return tags.filter(tag => tag.tag_type === "OFFER_NOTE");
  }

  render() {

    const { loading, offer, error, applicationExist, noOffer } = this.state;
    const t = this.props.t;

    if (loading) {
      return (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center">
          {error}
        </div>
      );
    }
    else if (offer !== null) {
      return this.displayOfferContent();
    }
    else if ((noOffer || offer === null) && !applicationExist) {
      return (
        <div className="text-base text-muted-foreground mt-8 text-center">
          {" "}
          {t("You did not apply to attend")}.
        </div>
      );
    }
    else {
      return (
        <div className="text-base text-muted-foreground mt-8 text-center">
          {" "}
          {t("Please await further communication")}
        </div>
      );
    }
  }
}

export default withRouter(withTranslation()(Offer));
