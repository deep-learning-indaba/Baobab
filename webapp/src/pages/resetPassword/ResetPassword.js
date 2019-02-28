import React, { Component } from "react";
import RequestPasswordResetForm from "./components/RequestPasswordResetForm.js"
import ConfirmPasswordResetForm from "./components/ConfirmPasswordResetForm.js"

export default class ResetPassword extends Component {
    constructor(props) {
        super(props);

        this.state = {
            resetToken: ""
        }
    }

    componentDidMount() {
        if (this.props.location.search) {
            this.setState({
                resetToken: this.props.location.search.substring(this.props.location.search.indexOf('=') + 1)
            });
        }
    }

    render() {
        if (this.state.resetToken) {
            return (
                <ConfirmPasswordResetForm token={this.state.resetToken}></ConfirmPasswordResetForm >
            );
        } else {
            return (
                <RequestPasswordResetForm></RequestPasswordResetForm>
            );
        }
    }
}