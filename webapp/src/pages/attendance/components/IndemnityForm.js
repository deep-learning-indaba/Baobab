
import React from "react";
import { attendanceService } from "../../../services/attendance/attendance.service";
import Loading from "../../../components/Loading";
import FormCheckbox from "../../../components/form/FormCheckbox";

class IndemnityForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      eventId: props.eventId,
      loading: true,
      agreed: false,
      submitting: false
    };
  }

  componentDidMount() {
    attendanceService
      .getIndemnityForm(this.state.eventId)
      .then(result => {
        this.setState({
          loading: false,
          data: result.data,
          error: result.error,
        });
      });
  }

  handleSubmit = (event) => {
    event.preventDefault();
    this.setState({submitting: true}, ()=> {
        attendanceService
            .postIndemnity(this.state.eventId)
            .then(result => {
                this.setState({
                    submitting: false,
                    data: result.data,
                    error: result.error
                })
            });
    });
  }

  handleChange = (e) => {
    if (e.target) {
        const value = e.target.checked | 0;
        this.setState({
            agreed: value
        });
    }
  }

  render() {
    const {data, loading, error, agreed, submitting} = this.state;

    if (loading) { return <Loading />; }

    if (error) {
        return (
            <div className={"alert alert-danger alert-container"}>
                {JSON.stringify(error)}
            </div>
        );
    }

    if (data.signed) {
        return <div className="alert alert-success alert-container">
            Thank you, you signed the indemnity form on {data.date}
        </div>
    }

    return <div>
        <h2>Indemnity Form for {data.event_name}</h2>
        <form onSubmit={this.handleSubmit}>
            <div className="card stretched indemnity-form">
                {data.indemnity_form}
            </div>
            <br/><br/>

            <FormCheckbox
                id="indemnity_agreed"
                name="indemnity_agreed"
                type="checkbox"
                label="I agree with the terms outlined in the indemnity form above."
                placeholder="I agree"
                onChange={this.handleChange}
                value={agreed}
                required={true} />
            <button
                id="btn-submit"
                type="submit"
                class="btn btn-primary"
                disabled={!agreed}>
                {submitting && (
                    <span
                    class="spinner-grow spinner-grow-sm"
                    role="status"
                    aria-hidden="true"
                    />
                )}
                Submit
            </button>
        </form>
    </div>
  }
}

export default IndemnityForm;
