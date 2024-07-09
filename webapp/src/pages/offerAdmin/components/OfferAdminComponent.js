import React, { Component } from "react";
import { withRouter } from "react-router";
import { offerServices } from "../../../services/offer/offer.service";
import { responsesService } from '../../../services/responses/responses.service';
import { withTranslation } from 'react-i18next';
import Loading from "../../../components/Loading";
import ReactTable from 'react-table';
import FormTextBox from "../../../components/form/FormTextBox";
import FormTextArea from "../../../components/form/FormTextArea";
import FormSelect from "../../../components/form/FormSelect";
import ReactToolTip from "react-tooltip";

/*
TODO:
- View a list of offers - DONE (add paid flag)
- Add a new offer
- Edit an existing offer (including tags)
- Delete an existing offer
- Extend an offer
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
            offerEditorVisible: false,
            selectedOffer: null,
            users: [],
            errors: [],
            isValid: true
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

        if (props.original.is_expired === true) {
            className = "badge badge-danger";
            text = t("Expired");
        }

        else if (props.original.candidate_response && props.original.is_paid) {
            className = "badge badge-success";
            text = t("Confirmed")
        }

        else if (props.original.candidate_response && !props.original.is_paid) {
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
                {this.props.original.is_paid ? <span className="badge badge-success">Paid</span> : ""}
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
              {props.original.tags.map(t => 
                  <span className="tag badge badge-primary" key={`tag_${props.original.response_id}_${t.id}`}>{t.name}</span>)}
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

    updateState = (offer) => {
        this.setState({
            updatedOffer: offer
        }, () => {
            const errors = this.validateOfferDetails();

            this.setState({
                errors: errors,
                isValid: errors.length === 0
            });
        });
    }

    renderOfferEditor = () => {
        const t = this.props.t;
        
    }

    render() {
        const { t } = this.props;
        const { loading, error, offers, offerEditorVisible } = this.state;
        console.log(offers);

        if (loading) { return <Loading />; }

        return (
            <div className="OfferAdmin container-fluid pad-top-30-md">
                {error &&
                    <div className={"alert alert-danger alert-container"}>
                    {JSON.stringify(error)}
                    </div>}

                <div className="card no-padding-h">
                    <p className="h4 text-center mb-4">{t("Offers")}</p>
                    <div className="react-table">
                        <ReactTable
                            className="ReactTable"
                            data={offers}
                            columns={this.getTableColumns()}
                            minRows={0}
                        />
                    </div>
                    {!offerEditorVisible && 
                        <div className={"row-mb-3"}>
                        <button
                            onClick={() => this.setOfferEditorVisible()}
                            className="btn btn-primary float-right margin-top-10px">
                            {t("New Offer")}
                        </button>
                        </div>
                    }
                    {offerEditorVisible && this.renderOfferEditor()}
                </div>
                <ReactToolTip id="tooltip" type="info" place="right" effect="solid" />
            </div>
        );
    }   
}

export default withTranslation()(withRouter(OfferAdminComponent));
