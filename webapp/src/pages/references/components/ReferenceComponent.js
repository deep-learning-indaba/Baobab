import React, { Component } from "react";
import { withRouter } from "react-router";
import { referenceService } from "../../../services/references";
import Loading from "../../../components/Loading";
import FileUploadComponent from "../../../components/FileUpload";

class ReferenceComponent extends Component {
    constructor(props) {
        super(props);
        this.state = {
            error: "",
            token: "",
            requestDetails: null,
            isLoading: true,
            uploadedDocument: "",
            isSubmitting: false,
            submitted: false,
            enableSubmit: false,
            success: false
        }
    }

    getDetails = () => {
        referenceService.getReferenceRequestDetails(this.props.match.params.token)
            .then(response => {
                this.setState({
                    requestDetails: response.details,
                    error: response.error,
                    isLoading: false,
                    submitted: response.details && !!response.details.reference_submitted_timestamp
                });
            });
    }

    componentDidMount() {
        if (this.props.match && this.props.match.params && this.props.match.params.token) {
            this.getDetails();
        }
        else {
            this.setState({
                error: "No token specified.",
                isLoading: false
            });
        }
    }

    onFileUploadChanged = (_, value) => {
        this.setState({
            uploadedDocument: value,
            enableSubmit: true
        });
    }

    submit = (event) => {
        this.setState({ isSubmitting: true });
        referenceService.submitReference(this.props.match.params.token, this.state.uploadedDocument, this.state.submitted).then(
            response => {
                this.setState({
                    error: response.error,
                    isSubmitting: false,
                    submitted: true,
                    enableSubmit: false,
                    success: true
                });
            });
    }

    render() {
        const { requestDetails, error, isLoading, uploadedDocument, isSubmitting, enableSubmit, success } = this.state;
        if (isLoading) { return <Loading />; }

        if (error) {
            return (
                <div className={"alert alert-danger alert-container"}>
                    {JSON.stringify(error)}
                </div>
            );
        }

        if (!requestDetails.is_application_open) {
            return (
                <div className={"alert alert-danger alert-container"}>
                    Unfortunately applications for {requestDetails.name} are now closed. If you still need to submit a reference for {requestDetails.candidate}, please <a href={`mailto:${requestDetails.email_from}`}>contact the event organisers</a>.
                </div>
            );
        }

        const nominationText = requestDetails.nominator
            ? `has been nominated by ${requestDetails.nominator}`
            : "has nominated themself"

        return (
            <div>
                <h1>Reference</h1>

                {requestDetails.reference_submitted_timestamp
                    && <div className="alert alert-success alert-container">
                        Thank you! You submitted your reference on {requestDetails.reference_submitted_timestamp}. You may update it below if you like.
                    </div>
                }

                <p>{requestDetails.candidate} {nominationText} for the {requestDetails.description}. Kindly upload your reference in support of their application in the form of a PDF (max 10Mb) below.</p>
                <div className="card stretched">
                    <h5>Upload Reference (PDF, 10Mb max)</h5>
                    <FileUploadComponent
                        id="file"
                        value={uploadedDocument}
                        onChange={this.onFileUploadChanged}
                        key="fileupload" />
                </div>

                {success &&
                    <div className={"alert alert-success alert-container"}>
                        Thank you! Your reference has been received and will be reviewed by our selection committee.
                    </div>
                }

                <button
                    type="submit"
                    class="btn btn-primary margin-top-32"
                    onClick={this.submit}
                    disabled={!enableSubmit}
                >
                    {isSubmitting && (
                        <span
                            class="spinner-grow spinner-grow-sm"
                            role="status"
                            aria-hidden="true" />
                    )}
                    Submit reference
                    </button>
            </div>
        );

    }
}

export default withRouter(ReferenceComponent); 