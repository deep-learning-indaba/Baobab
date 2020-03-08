import React, { Component } from "react";
import { withRouter } from "react-router";
import { referenceService } from "../../../services/references";
import Loading from "../../../components/Loading";
import FileUploadComponent from "../../../components/FileUpload";

// TODO: Update back-end to format candidate into a single string and populate with AppUser information for self-nominations
// TODO: Add referer details to ReferenceRequestDetails

const DUMMY_DATA = {
    candidate: 'Mx Boaty McBoatface',
    relation: 'Cousin',
    name: 'Kambule Masters Award',
    description: 'The Kambule Masters Dissertation Award',
    is_application_open: true,
    email_from: 'awards@deeplearningindaba.com',
    reference_submitted_timestamp: null
}

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
            submitted: false
        }
    }

    getDetails = () => {
        referenceService.getReferenceRequestDetails(this.props.match.params.token)
            .then(response => {
                this.setState({
                    requestDetails: DUMMY_DATA, // response.details,
                    error: "", // response.error,
                    isLoading: false
                })
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
            uploadedDocument: value
        });
    }

    submit = (event) => {
        this.setState({ isSubmitting: true });
        referenceService.submitReference(this.state.token, this.state.uploadedDocument).then(
            response => {
                this.setState({
                    error: response.error,
                    isSubmitting: false,
                    submitted: true,
                    uploadedDocument: ""
                })
            });
    }

    render() {
        const { requestDetails, error, isLoading, uploadedDocument, isSubmitting } = this.state;
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

        return (
            <div>
                <h1>Reference</h1>

                {requestDetails.reference_submitted_timestamp
                    && <div className="card flat-card success stretched">
                        Thank you! You submitted your reference on {requestDetails.reference_submitted_timestamp}. You may update it below if you like.
                    </div>
                }

                {/* TODO: Add details about nominator and nominee when it's not a self-nomination */}
                <p>{requestDetails.candidate} has requested your reference in support of their application to the {requestDetails.description}. Kindly upload your reference in the form of a PDF (max 10Mb) below.</p>
                <div className="card stretched">
                    <h5>Upload Reference (PDF, 10Mb max)</h5>
                    <FileUploadComponent
                        id="file"
                        value={uploadedDocument}
                        onChange={this.onFileUploadChanged}
                        key="fileupload" />
                </div>

                <button
                    type="submit"
                    class="btn btn-primary margin-top-32"
                    onClick={this.submit}
                    disabled={!uploadedDocument}
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