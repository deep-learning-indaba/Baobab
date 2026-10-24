import React, { Component } from "react";
import { withRouter } from "react-router";
import { offerServices } from "../../../services/offer/offer.service";
import { withTranslation } from 'react-i18next';
import ReactTable from 'react-table';
import FormTextBox from "../../../components/form/FormTextBox";
import FormSelect from "../../../components/form/FormSelect";
import ReactToolTip from "react-tooltip";
import FormDate from "../../../components/form/FormDate";
import { formatUserName } from "../../../utils/userName";
import { tagsService } from "../../../services/tags/tags.service";
import { ConfirmModal } from "../../../components/Modal";
import FormCheckbox from "../../../components/form/FormCheckbox";

const todayString = () => new Date().toISOString().slice(0, 10);

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
            selectedResponseFilter: "all",
            editorMode: "edit",
            candidates: [],
            eventFees: [],
            eventTags: [],
            newOffer: null,
            tagPickerKey: 0,
            resetModalVisible: false,
            saving: false
        };
    }

    componentDidMount() {
        const eventId = this.props.event.id;
        Promise.all([
            offerServices.getOfferList(eventId),
            offerServices.getOfferCandidates(eventId),
            tagsService.getTagList(eventId, this.props.i18n.language)
        ]).then(([offerResponse, candidateResponse, tagResponse]) => {
            const offers = offerResponse.offers || [];
            this.setState({
                loading: false,
                offers: offers,
                filteredOffers: offers,
                candidates: candidateResponse.candidates,
                eventFees: candidateResponse.eventFees,
                eventTags: (tagResponse.tags || []).filter(tag =>
                    tag.active && (tag.tag_type === "GRANT" || tag.tag_type === "OFFER_NOTE")),
                error: offerResponse.error || candidateResponse.error || tagResponse.error
            });
        });
    }

    applyFilters = (offers, search, responseFilter) => {
        const term = search.toLowerCase();
        return offers.filter(o => {
            const matchesSearch = !term ||
                o.firstname.toLowerCase().includes(term) ||
                o.lastname.toLowerCase().includes(term) ||
                o.email.toLowerCase().includes(term);
            const matchesResponse = responseFilter === "all" ||
                String(o.candidate_response) === responseFilter;
            return matchesSearch && matchesResponse;
        });
    }

    replaceOffer = (updatedOffer) => {
        const offers = this.state.offers.map(o => o.id === updatedOffer.id ? updatedOffer : o);
        return {
            offers: offers,
            filteredOffers: this.applyFilters(offers, this.state.search, this.state.selectedResponseFilter)
        };
    }

    refreshCandidates = () => {
        offerServices.getOfferCandidates(this.props.event.id).then(response => {
            this.setState({ candidates: response.candidates, eventFees: response.eventFees });
        });
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
            editorMode: "edit",
            selectedOffer: offer,
            updated: false,
            isValid: true,
            errors: [],
            error: ""
        });
    }

    addOffer = () => {
        this.setState({
            offerEditorVisible: true,
            editorMode: "create",
            selectedOffer: null,
            newOffer: {
                user_id: null,
                expiry_date: "",
                payment_required: false,
                event_fee_id: null,
                tags: []
            },
            updated: false,
            isValid: false,
            errors: [],
            error: ""
        });
    }

    closeEditor = () => {
        this.setState({ offerEditorVisible: false, selectedOffer: null, newOffer: null, updated: false });
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
                {formatUserName(u.user_title, u.firstname, u.lastname)}
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
            minWidth: 90
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
              <button className="link-button" onClick={() => this.editOffer(props.original)} aria-label={this.props.t("Edit Offer")}><i className="fa fa-edit"></i></button>
            </div>,
            minWidth: 50,
            maxWidth: 60
          }
        ];

        return columns;
    } 

    getEditedOffer = () => this.state.editorMode === "create" ? this.state.newOffer : this.state.selectedOffer;

    setEditedOffer = (offer) => {
        const key = this.state.editorMode === "create" ? "newOffer" : "selectedOffer";
        this.setState({ [key]: offer, updated: true }, () => {
            const errors = this.validateOfferDetails();
            this.setState({ errors: errors, isValid: errors.length === 0 });
        });
    }

    setOfferExpiry = (expiry_date) => {
        this.setEditedOffer({ ...this.getEditedOffer(), expiry_date: expiry_date });
    }

    setCandidate = (id, selected) => {
        this.setEditedOffer({ ...this.getEditedOffer(), user_id: selected.value });
    }

    setPaymentRequired = (e) => {
        const payment_required = e.target.checked;
        this.setEditedOffer({
            ...this.getEditedOffer(),
            payment_required: payment_required,
            event_fee_id: payment_required ? this.getEditedOffer().event_fee_id : null
        });
    }

    setEventFee = (id, selected) => {
        this.setEditedOffer({ ...this.getEditedOffer(), event_fee_id: selected.value });
    }

    addTagToOffer = (id, selected) => {
        const offer = this.getEditedOffer();
        const tag = this.state.eventTags.find(tg => tg.id === selected.value);
        this.setState({ tagPickerKey: this.state.tagPickerKey + 1 });
        this.setEditedOffer({ ...offer, tags: [...offer.tags, { ...tag, accepted: null }] });
    }

    removeTagFromOffer = (tagId) => {
        const offer = this.getEditedOffer();
        this.setEditedOffer({ ...offer, tags: offer.tags.filter(tag => tag.id !== tagId) });
    }

    validateOfferDetails = () => {
        const { t } = this.props;
        const offer = this.getEditedOffer();
        const errors = [];

        if (this.state.editorMode === "create") {
            if (!offer.user_id) {
                errors.push(t("Select a candidate"));
            }
            if (offer.payment_required && !offer.event_fee_id) {
                errors.push(t("Select a fee for the offer"));
            }
        }
        if (!offer.expiry_date) {
            errors.push(t("Enter an expiry date"));
        }
        else if (this.state.editorMode === "create" && offer.expiry_date < todayString()) {
            errors.push(t("The expiry date must not be in the past"));
        }
        return errors;
    }

    tagsOfType = (tags, tagType) => tags.filter(tag => tag.tag_type === tagType).map(tag => ({ id: tag.id }));

    saveOffer = () => {
        if (this.state.editorMode === "create") {
            this.createOffer();
            return;
        }

        const { selectedOffer } = this.state;
        this.setState({ saving: true });
        offerServices.updateOfferAdmin({
            id: selectedOffer.id,
            event_id: this.props.event.id,
            expiry_date: selectedOffer.expiry_date,
            grant_tags: this.tagsOfType(selectedOffer.tags, "GRANT"),
            note_tags: this.tagsOfType(selectedOffer.tags, "OFFER_NOTE")
        }).then(response => {
            if (response.error) {
                this.setState({ error: response.error, saving: false });
            }
            else {
                this.setState({
                    ...this.replaceOffer(response.offer),
                    selectedOffer: response.offer,
                    updated: false,
                    saving: false,
                    error: ""
                });
            }
        });
    }

    createOffer = () => {
        const { newOffer } = this.state;
        this.setState({ saving: true });
        offerServices.addOffer(
            newOffer.user_id,
            this.props.event.id,
            new Date().toISOString(),
            `${newOffer.expiry_date}T23:59:59.000Z`,
            newOffer.payment_required,
            this.tagsOfType(newOffer.tags, "GRANT"),
            this.tagsOfType(newOffer.tags, "OFFER_NOTE"),
            newOffer.event_fee_id
        ).then(response => {
            if (response.error) {
                this.setState({ error: response.error, saving: false });
                return;
            }
            const offers = [...this.state.offers, response.offer];
            this.setState({
                offers: offers,
                filteredOffers: this.applyFilters(offers, this.state.search, this.state.selectedResponseFilter),
                offerEditorVisible: false,
                newOffer: null,
                updated: false,
                saving: false,
                error: ""
            });
            this.refreshCandidates();
        });
    }

    expiryHasPassed = (offer) => offer.expiry_date < todayString();

    resetOffer = () => {
        const { selectedOffer, updated } = this.state;
        this.setState({ resetModalVisible: false, saving: true });
        offerServices.resetOffer(
            selectedOffer.id,
            this.props.event.id,
            updated ? selectedOffer.expiry_date : null
        ).then(response => {
            if (response.error) {
                this.setState({ error: response.error, saving: false });
            }
            else {
                this.setState({
                    ...this.replaceOffer(response.offer),
                    selectedOffer: response.offer,
                    updated: false,
                    saving: false,
                    error: response.offer.email_sent === false
                        ? this.props.t("The offer was reset, but the notification email could not be sent to the candidate.")
                        : ""
                });
            }
        });
    }

    renderResetModal = () => {
        const { t } = this.props;
        const { selectedOffer, resetModalVisible } = this.state;
        if (!resetModalVisible) {
            return null;
        }
        return (
            <ConfirmModal
                visible={resetModalVisible}
                onOK={this.resetOffer}
                onCancel={() => this.setState({ resetModalVisible: false })}
                okText={t("Reset Offer")}
                cancelText={t("Cancel")}>
                <p>
                    {t("Reset the rejected offer for {{name}}? The rejection will be cleared and the candidate will be emailed so they can respond to the offer again.", {
                        name: formatUserName(selectedOffer.user_title, selectedOffer.firstname, selectedOffer.lastname)
                    })}
                </p>
            </ConfirmModal>
        );
    }

    updateSearch = (event) => {
        const search = event.target.value;
        this.setState({
            search: search,
            filteredOffers: this.applyFilters(this.state.offers, search, this.state.selectedResponseFilter)
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
        this.setState({
            selectedResponseFilter: selectedResponseFilter,
            filteredOffers: this.applyFilters(this.state.offers, this.state.search, selectedResponseFilter)
        });
    }

    renderTagEditor = (offer) => {
        const { t } = this.props;
        const attachedIds = offer.tags.map(tag => tag.id);
        const options = this.state.eventTags
            .filter(tag => !attachedIds.includes(tag.id))
            .map(tag => ({
                value: tag.id,
                label: `${tag.name} (${tag.tag_type === "GRANT" ? t("Grant") : t("Note")})`
            }));

        return (
            <div className="space-y-2">
                <label className="block text-sm font-semibold text-foreground/90">{t("Tags")}</label>
                <div className="flex flex-wrap gap-1 items-center">
                    {offer.tags.length === 0 && <span className="text-sm text-foreground/60">{t("No tags")}</span>}
                    {offer.tags.map(tag => (
                        <span className={"inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border " + (tag.tag_type === "OFFER_NOTE" ? "bg-warning/10 text-warning-text border-warning-border/50" : "bg-primary/10 text-primary border-primary/20")} key={`tag_${offer.id}_${tag.id}`}>
                            {tag.name}
                            <button
                                type="button"
                                className="cursor-pointer leading-none opacity-70 hover:opacity-100"
                                aria-label={t("Remove tag {{name}}", { name: tag.name })}
                                onClick={() => this.removeTagFromOffer(tag.id)}>
                                &times;
                            </button>
                        </span>
                    ))}
                </div>
                <FormSelect
                    key={this.state.tagPickerKey}
                    id="offerTagPicker"
                    options={options}
                    placeholder={t("Add a tag")}
                    onChange={this.addTagToOffer}
                    value={null} />
            </div>
        );
    }

    renderCreateFields = () => {
        const { t } = this.props;
        const { newOffer, candidates, eventFees } = this.state;
        const candidateOptions = candidates.map(c => ({
            value: c.user_id,
            label: `${formatUserName(c.user_title, c.firstname, c.lastname)} (${c.email})`
        }));
        const feeOptions = eventFees.map(f => ({
            value: f.id,
            label: `${f.name} - ${f.amount} ${f.iso_currency_code}`
        }));

        return (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
                <div className="space-y-2 md:col-span-2">
                    <label htmlFor="offerCandidate" className="block text-sm font-semibold text-foreground/90">{t("Candidate")}</label>
                    <FormSelect
                        id="offerCandidate"
                        options={candidateOptions}
                        placeholder={candidates.length ? t("Select a candidate") : t("No candidates available for an offer")}
                        searchable={true}
                        onChange={this.setCandidate}
                        value={newOffer.user_id} />
                </div>

                <div className="space-y-2">
                    <label htmlFor="expiry_date" className="block text-sm font-semibold text-foreground/90">{t("Expiry Date")}</label>
                    <FormDate id="expiry_date" value={newOffer.expiry_date} onChange={this.setOfferExpiry} fieldName="expiry_date" />
                </div>

                <div className="space-y-2">
                    <label className="block text-sm font-semibold text-foreground/90">{t("Payment")}</label>
                    <FormCheckbox
                        id="paymentRequired"
                        label={t("Payment required")}
                        value={newOffer.payment_required}
                        onChange={this.setPaymentRequired} />
                    {newOffer.payment_required && (
                        <FormSelect
                            id="offerEventFee"
                            options={feeOptions}
                            placeholder={t("Select a fee")}
                            onChange={this.setEventFee}
                            value={newOffer.event_fee_id} />
                    )}
                </div>

                {this.renderTagEditor(newOffer)}
            </div>
        );
    }

    renderEditFields = () => {
        const t = this.props.t;
        const { selectedOffer } = this.state;

        return (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
                <div className="space-y-2">
                    <label className="block text-sm font-semibold text-foreground/90">{t("Offer Date")}</label>
                    <FormDate id="offer_date" value={selectedOffer.offer_date} fieldName="offer_date" disabled={true}/>
                </div>

                <div className="space-y-2">
                    <label htmlFor="expiry_date" className="block text-sm font-semibold text-foreground/90">{t("Expiry Date")}</label>
                    <FormDate id="expiry_date" value={selectedOffer.expiry_date} onChange={this.setOfferExpiry} fieldName="expiry_date" />
                </div>

                {this.renderTagEditor(selectedOffer)}

                <div className="space-y-2">
                    <label className="block text-sm font-semibold text-foreground/90">{t("Response")}</label>
                    <div className="text-sm text-foreground">{this.candidateResponseCell({original: selectedOffer})}</div>
                </div>

                {selectedOffer.responded_at && (
                    <div className="space-y-2">
                        <label className="block text-sm font-semibold text-foreground/90">{t("Responded At")}</label>
                        <div className="text-sm text-foreground">{selectedOffer.responded_at}</div>
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
        );
    }

    renderOfferEditor = () => {
        const t = this.props.t;
        const { selectedOffer, editorMode, errors, updated, isValid, saving } = this.state;
        const isCreate = editorMode === "create";
        const canReset = !isCreate && selectedOffer.candidate_response === false;
        const resetBlocked = canReset && this.expiryHasPassed(selectedOffer);

        return (
            <div className="bg-slate-50/50 rounded-xl border border-border p-6 space-y-6 mt-6">
                <div className="flex justify-between items-center pb-2 border-b border-border/50">
                    <h3 className="text-lg font-bold text-foreground">
                        {isCreate
                            ? t("New Offer")
                            : <>{t("Offer for")} {formatUserName(selectedOffer.user_title, selectedOffer.firstname, selectedOffer.lastname)}</>}
                    </h3>
                    {!isCreate && <span className="text-sm font-semibold">{this.statusCell({original: selectedOffer})}</span>}
                </div>

                {isCreate ? this.renderCreateFields() : this.renderEditFields()}

                {updated && errors.length > 0 && (
                    <ul className="text-sm text-error text-left list-disc pl-5">
                        {errors.map(e => <li key={e}>{e}</li>)}
                    </ul>
                )}

                <div className="flex justify-between items-center pt-4 border-t border-border/50 gap-3">
                    <div className="text-left">
                        {canReset && (
                            <>
                                <button
                                    className="inline-flex items-center justify-center px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-secondary text-secondary-foreground hover:bg-secondary/80 disabled:opacity-50 cursor-pointer"
                                    onClick={() => this.setState({ resetModalVisible: true })}
                                    disabled={resetBlocked || saving}>
                                    {t("Reset Offer")}
                                </button>
                                {resetBlocked && (
                                    <p className="text-xs text-foreground/60 mt-1">{t("Set a new expiry date in the future to reset this offer.")}</p>
                                )}
                            </>
                        )}
                    </div>
                    <div className="flex gap-3">
                        <button
                            className="inline-flex items-center justify-center px-4 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-secondary text-secondary-foreground hover:bg-secondary/80 cursor-pointer"
                            onClick={this.closeEditor}>
                            {t("Cancel")}
                        </button>
                        <button 
                            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50 cursor-pointer" 
                            onClick={() => this.saveOffer()}
                            disabled={!isValid || !updated || saving}
                        >
                            {isCreate ? t("Create Offer") : t("Save")}
                        </button>
                    </div>
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
            <div className="w-full pt-6 text-left space-y-6">
                {error && (
                    <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
                        {typeof error === "string" ? error : JSON.stringify(error)}
                    </div>
                )}

                <div className="bg-white rounded-2xl shadow-sm border border-border p-8 space-y-6" key="tag-table">
                    <div className="flex justify-between items-center mb-6">
                        <h1 className="font-heading text-2xl font-bold text-foreground">{t("Offers")}</h1>
                        <button
                            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm cursor-pointer"
                            onClick={this.addOffer}>
                            {t("Add Offer")}
                        </button>
                    </div>

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
                {this.renderResetModal()}
                <ReactToolTip id="tooltip" type="info" place="right" effect="solid" />
            </div>
        );
    }   
}

export default withTranslation()(withRouter(OfferAdminComponent));
