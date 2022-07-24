import React, { Component } from "react";
import { withRouter } from "react-router";
import { invoiceService } from "../../../services/invoices";
import Loading from "../../../components/Loading";

class PaymentComponent extends Component {
    constructor(props) {
        super(props);
        this.state = {
            error: "",
            paymentInfo: null,
            isLoading: true
        }
    }

    componentDidMount() {
        if (this.props.match && this.props.match.params && this.props.match.params.invoiceId) {
            this.initiatePayment();
        }
        else {
            this.setState({
                error: "No invoice specified.",
                isLoading: false
            });
        }
    }

    initiatePayment = () => {
        console.log("match params:", this.props.match.params);
        console.log("invoiceId:", this.props.match.params.invoiceId);
        invoiceService.initiatePayment(this.props.match.params.invoiceId)
            .then(response => {
                this.setState({
                    paymentInfo: response.paymentInfo,
                    error: response.error,
                    isLoading: false
                }, () => {
                    if (this.state.paymentInfo) {
                        window.location.replace(this.state.paymentInfo.url);
                    }
                });
            });
    }

    render() {
        const { paymentInfo, error, isLoading } = this.state;
        
        if (isLoading) { return <Loading />; }

        if (error) {
            return (
                <div className={"alert alert-danger alert-container"}>
                    {JSON.stringify(error)}
                </div>
            );
        }

        return (
            <div>
                <p>Redirecting you to Stripe to complete payment. If you are not automatically redirected, please <a href={paymentInfo.url}>click here</a>.</p>
            </div>
        );
    }
}

export default withRouter(PaymentComponent); 
