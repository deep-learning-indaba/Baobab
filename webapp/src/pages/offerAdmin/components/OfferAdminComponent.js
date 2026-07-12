import React, { Component } from "react";
import { withRouter } from "react-router";
import { offerServices } from "../../../services/offer/offer.service";
import { withTranslation } from 'react-i18next';
import ReactTable from 'react-table';
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import ReactToolTip from "react-tooltip";
import FormDate from "../../../components/form/FormDate";

/*
TODO:
- View a list of offers - DONE (add paid flag)
- Add a new offer
- Edit an existing offer (including tags)
- Delete an existing offer
- Extend an offer  - DONE 
- Filter offers by candidate response
- Filter offers by tags
- Filter offers by expiry
- Filter offers by payment required
- Filter offers by candidate name
- Filter offers by candidate email
- Maybe don't allow removing tags in the table? (only in the edit section) to make it safer.
*/

class OfferAdminComponent extends Component {
    constructor(props) {
        super(props);

        this.state = {
            loading: true,
            error: "",
            offers: [],
            filteredOffers: [],
            offerEditorVisible: false,
            selectedOffer: null,
            users: [],
            errors: [],
            isValid: true,
            updated: false,
            search: "",
            selectedResponseFilter: "all"
        };
    }

    componentDidMount() {
        Promise.all([
            offerServices.getOfferList(this.props.event.id),
            //responsesService.getResponseList(this.props.event.id, false, [])
        ]).then(([offerResponse]) => {
            const offers = offerResponse.offers || [];
            //const offerUsers = offers.map(o => o.user_id);
            this.setState({
                loading: false,
                offers: offers,
                filteredOffers: offers,
                error: offerResponse.error //|| responseResponse.error,
                // users: (responseResponse.responses || [])
                //     .filter(r => !offerUsers.includes(r.user_id))
                //     .map(r => ({
                //         userId: r.user_id,
                //         name: r.user_title + " " + r.firstname + " " + r.lastname,
                //         email: r.email    
                //     }))
            });
        });
    }

    addTag = (offer) => {
        // TODO
    }

    removeTag = (offer, tag) => {
        // TODO
    }

    candidateResponseCell = (props) => {
        const {t} = this.props;
        let className = "badge badge-secondary";
        let text = t("No Response");
        let description = "";

        if (props.original.candidate_response === true) {
            className = "badge badge-success";
            text = t("Accepted");
        }
        else if (props.original.candidate_response === false) {
            className = "badge badge-danger";
            text = t("Rejected");
            description = props.original.rejected_reason;
        }

        return <div>
            <span className={className}>{text}</span> <span data-tooltip-id="tooltip" data-tooltip-content={description}>{description}</span>
        </div>
    }

    statusCell = (props) => {
        const {t} = this.props;
        let className = "badge badge-secondary";
        let text = t("Pending");
        
        if (props.original.candidate_response === false)  {
            className = "badge badge-danger";
            text = t("Rejected");
        }

        else if (props.original.is_expired === true) {
            className = "badge badge-danger";
            text = t("Expired");
        }

        else if (props.original.candidate_response && props.original.is_confirmed) {
            className = "badge badge-success";
            text = t("Confirmed")
        }

        else if (props.original.candidate_response && !props.original.is_confirmed) {
            className = "badge badge-warning";
            text = t("Payment Pending")
        }

        return <span className={className}>{text}</span>;
    }

    editOffer = (offer) => {
        this.setState({
            offerEditorVisible: true,
            selectedOffer: offer
        });
    }

    paymentCell = (props) => {
        if (props.original.payment_required === true) {
            return <span>
                {props.original.payment_amount} {this.props.organisation.iso_currency_code === "None" ? "" : this.props.organisation.iso_currency_code} 
                {props.original.is_paid ? <span className="badge badge-success">Paid</span> : ""}
                </span>;
        }
        else {
            return "-";
        }
    }

    getTableColumns = () => {
        const {t} = this.props;

        const columns = [{
            id: "user",
            Header: <div className="fullname">{t("Full Name")}</div>,
            accessor: u =>
              <div className="fullname">
                {u.user_title + " " + u.firstname + " " + u.lastname}
              </div>,
            minWidth: 150
        }, {
            id: "email",
            Header: <div className="email">{t("Email")}</div>,
            accessor: u => u.email,
            minWidth: 150
        }, {
            id: "tags",
            Header: <div className="tags">{t("Tags")}</div>,
            Cell: props => <div>
              {props.original.tags.map(tag => 
                  <span className={"tag badge " + (tag.tag_type === "OFFER_NOTE" ? "badge-warning" : "badge-primary")} key={`tag_${props.original.response_id}_${tag.id}`}>{tag.name}</span>)}
            </div>,
            accessor: u => u.tags.map(t => t.name).join("; "),
            minWidth: 150
          },
          {
            id: "offer_date",
            Header: <div className="offer-date">{t("Offer Date")}</div>,
            accessor: u => u.offer_date,
            minWidth: 80
          },
          {
            id: "expiry_date",
            Header: <div className="expiry-date">{t("Expiry Date")}</div>,
            accessor: u => u.expiry_date,
            minWidth: 80
          },
          {
            id: "payment",
            Header: <div className="payment-amount">{t("Payment")}</div>,
            accessor: u => u.payment_amount,
            Cell: this.paymentCell,
            minWidth: 150
          },
          {
            id: "candidate_response",
            Header: <div className="candidate-response">{t("Response")}</div>,
            accessor: u => u.candidate_response,
            Cell: this.candidateResponseCell,
            minWidth: 80
          },
          {
            id: "status",
            Header: <div className="status">{t("Status")}</div>,
            accessor: u => u.is_expired,
            Cell: this.statusCell,
            minWidth: 80
          },
          {
            id: "actions",
            Header: "",
            Cell: props => <div>
              <button className="link-button" onClick={() => this.editOffer(props.original)}><i className="fa fa-edit"></i></button>
            </div>,
            minWidth: 150
          }
        ];

        return columns;
    } 

    setOfferEditorVisible = () => {
        this.setState({
            offerEditorVisible: true
        });
    };

    setOfferExpiry = (expiry_date) => {
        const u = {
            ...this.state.selectedOffer,
            expiry_date: expiry_date
        };
        this.updateState(u);
    }

    updateDropDown = (fieldName, dropdown) => {
        const u = {
          ...this.state.updatedTag,
          [fieldName]: dropdown.value
        };
        this.updateState(u);
      };

    validateOfferDetails = () => {
        return [];
    }

    saveOffer = () => {
        const { selectedOffer } = this.state;
        offerServices.updateOfferAdmin(selectedOffer).then(response => {
            if (response.error) {
                this.setState({
                    error: response.error
                });
            }
            else {
                this.setState({
                    offerEditorVisible: false,
                    updated: false,
                    offers: this.state.offers.map(o => o.id === selectedOffer.id ? selectedOffer : o)
                });
            }
        });
    }

    updateState = (offer) => {
        this.setState({
            selectedOffer: offer,
            updated: true
        }, () => {
            const errors = this.validateOfferDetails();

            this.setState({
                errors: errors,
                isValid: errors.length === 0
            });
        });
    }

    updateSearch = (event) => {
        const search = event.target.value;
        this.setState({
            search: search,
            filteredOffers: this.state.offers.filter(o => o.firstname.toLowerCase().includes(search.toLowerCase()) || o.lastname.toLowerCase().includes(search.toLowerCase()) || o.email.toLowerCase().includes(search.toLowerCase()))
        });
    }

    getCandidateResponseOptions = () => {
        return [{ value: "all", label: this.props.t("All") }, 
                { value: "true", label: this.props.t("Accepted") }, 
                { value: "false", label: this.props.t("Rejected") },
                { value: "null", label: this.props.t("No Response") }];
    }

    updateResponseFilter = (id, selected) => {
        const selectedResponseFilter = selected.value;
        let filteredOffers = this.state.offers;

        if (selectedResponseFilter === "true") {
            filteredOffers = this.state.offers.filter(o => o.candidate_response === true);
        }
        else if (selectedResponseFilter === "false") {
            filteredOffers = this.state.offers.filter(o => o.candidate_response === false);
        }
        else if (selectedResponseFilter === "null") {
            filteredOffers = this.state.offers.filter(o => o.candidate_response === null);
        }

        this.setState({
            selectedResponseFilter: selectedResponseFilter,
            filteredOffers: filteredOffers
        });
    }

    renderOfferEditor = () => {
        const t = this.props.t;
        const { selectedOffer } = this.state;
        return (
            <div className="bg-slate-50/50 rounded-xl border border-border p-6 space-y-6 mt-6">
                <div className="flex justify-between items-center pb-2 border-b border-border/50">
                    <h3 className="text-lg font-bold text-foreground">
                        {t("Offer for")} {selectedOffer.user_title + " " + selectedOffer.firstname + " " + selectedOffer.lastname}
                    </h3>
                    <span className="text-sm font-semibold">{this.statusCell({original: selectedOffer})}</span>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
                    <div className="space-y-2">
                        <label className="block text-sm font-semibold text-foreground/90">{t("Offer Date")}</label>
                        <FormDate id="expiry_date" value={selectedOffer.offer_date} fieldName="expiry_date" disabled={true}/>
                    </div>

                    <div className="space-y-2">
                        <label htmlFor="expiry_date" className="block text-sm font-semibold text-foreground/90">{t("Expiry Date")}</label>
                        <FormDate id="expiry_date" value={selectedOffer.expiry_date} onChange={this.setOfferExpiry} fieldName="expiry_date" />
                    </div>

                    <div className="space-y-2">
                        <label className="block text-sm font-semibold text-foreground/90">{t("Tags")}</label>
                        <div className="flex flex-wrap gap-1 items-center">
                            {selectedOffer.tags.map(tag => (
                                <span className={"inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border " + (tag.tag_type === "OFFER_NOTE" ? "bg-warning/10 text-warning-text border-warning-border/50" : "bg-primary/10 text-primary border-primary/20")} key={`tag_${selectedOffer.response_id}_${tag.id}`}>
                                    {tag.name}
                                </span>
                            ))}
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="block text-sm font-semibold text-foreground/90">{t("Response")}</label>
                        <div className="text-sm text-foreground">{this.candidateResponseCell({original: selectedOffer})}</div>
                    </div>

                    {selectedOffer.response_date && (
                        <div className="space-y-2">
                            <label className="block text-sm font-semibold text-foreground/90">{t("Responded At")}</label>
                            <div className="text-sm text-foreground">{selectedOffer.response_date}</div>
                        </div>
                    )}

                    {selectedOffer.candidate_response === false && (
                        <div className="space-y-2">
                            <label className="block text-sm font-semibold text-foreground/90">{t("Rejected Reason")}</label>
                            <div className="text-sm text-foreground italic bg-slate-100/50 border border-border rounded-lg p-3">{selectedOffer.rejected_reason}</div>
                        </div>
                    )}

                    <div className="space-y-2">
                        <label className="block text-sm font-semibold text-foreground/90">{t("Payment")}</label>
                        <div className="text-sm text-foreground">{this.paymentCell({original: selectedOffer})}</div>
                    </div>
                </div>

                <div className="flex justify-end pt-4 border-t border-border/50">
                    <button 
                        className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50 cursor-pointer" 
                        onClick={() => this.saveOffer()}
                        disabled={!this.state.isValid || !this.state.updated}
                    >
                        {t("Save")}
                    </button>
                </div>
            </div>
        );
    }

    render() {
        const { t } = this.props;
        const { loading, error, filteredOffers, offerEditorVisible } = this.state;

        if (loading) {
            return (
                <div className="flex justify-center items-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            );
        }

        return (
            <div className="w-full max-w-5xl mx-auto pt-6 text-left space-y-6">
                {error && (
                    <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
                        {JSON.stringify(error)}
                    </div>
                )}

                <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6" key="tag-table">
                    <h1 className="font-heading text-2xl font-bold text-foreground mb-6">{t("Offers")}</h1>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <FormTextBox
                                id="s"
                                type="text"
                                placeholder={t("Search")}
                                onChange={this.updateSearch}
                                label={t("Filter by name or email")}
                                name=""
                                value={this.state.search} />
                        </div>
                        <div className="space-y-2">
                            <FormSelect
                                options={this.getCandidateResponseOptions()}
                                id="candidateResponseFilter"
                                placeholder={t("Candidate Response")}
                                onChange={this.updateResponseFilter}
                                label={t("Filter by candidate response")}
                                defaultValue={this.state.selectedResponseFilter || "all"}
                                value={this.state.selectedResponseFilter || "all"} />
                        </div>
                    </div>

                    <div className="react-table">
                        <ReactTable
                            className="ReactTable"
                            data={filteredOffers}
                            columns={this.getTableColumns()}
                            minRows={0}
                        />
                    </div>
                </div>
                {offerEditorVisible && this.renderOfferEditor()}
                <ReactToolTip id="tooltip" type="info" place="right" effect="solid" />
            </div>
        );
    }   
}

export default withTranslation()(withRouter(OfferAdminComponent));
