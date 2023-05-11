import React, { Component } from "react";
import { withRouter } from "react-router";
import { offerServices } from "../../../services/offer/offer.service";
import { withTranslation } from 'react-i18next';
import Loading from "../../../components/Loading";
import ReactTable from 'react-table';

/*
TODO:
- View a list of offers - DONE
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
            offers: []
        };
    }

    componentDidMount() {
        offerServices.getOfferList(this.props.event.id).then(response => {
            this.setState({
                loading: false,
                offers: response.offers || [],
                error: response.error
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

        if (props.original.candidate_response === true) {
            className = "badge badge-success";
            text = t("Accepted");
        }
        else if (props.original.candidate_response === false) {
            className = "badge badge-danger";
            text = t("Rejected");
        }

        return <div>
            <span className={className}>{text}</span>
        </div>
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
                  <span className="tag badge badge-primary" onClick={()=>this.removeTag(props.original, t)} key={`tag_${props.original.response_id}_${t.id}`}>{t.name}</span>)}
              <i className="fa fa-plus-circle" onClick={() => this.addTag(props.original)}></i>
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
            id: "candidate_response",
            Header: <div className="candidate-response">{t("Response")}</div>,
            accessor: u => u.candidate_response,
            Cell: this.candidateResponseCell,
            minWidth: 80
          },
          {
            id: "payment_required",
            Header: <div className="payment-required">{t("Payment Required")}</div>,
            accessor: u => u.payment_required,
            minWidth: 150
          },
          {
            id: "payment_amount",
            Header: <div className="payment-amount">{t("Payment Amount")}</div>,
            accessor: u => u.payment_amount,
            minWidth: 150
          },
          {
            id: "rejected_reason",
            Header: <div className="rejected-reason">{t("Rejected Reason")}</div>,
            accessor: u => u.rejected_reason,
            minWidth: 150
          }
        ];

        return columns;
    }

    render() {
        const { t } = this.props;
        const { loading, error, offers } = this.state;
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
                </div>
            </div>
        );
    }   
}

export default withTranslation()(withRouter(OfferAdminComponent));
