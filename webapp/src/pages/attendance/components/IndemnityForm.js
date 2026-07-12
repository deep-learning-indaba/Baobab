
import React from "react";
import { attendanceService } from "../../../services/attendance/attendance.service";
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

    if (loading) {
      return (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      );
    }

    if (error) {
        return (
            <div className="bg-error/10 text-error border border-error/20 p-4 rounded-xl text-sm w-full text-center mt-6">
                {JSON.stringify(error)}
            </div>
        );
    }

    if (data.signed) {
        return (
            <div className="bg-green-50 text-green-800 border border-green-200 p-6 rounded-2xl shadow-sm mt-6 text-center">
                Thank you, you signed the indemnity form on {data.date}
            </div>
        );
    }

    return (
      <div className="w-full max-w-5xl mx-auto pt-6 text-left">
        <h1 className="font-heading text-2xl font-bold text-foreground mb-6">Indemnity Form for {data.event_name}</h1>
        <form onSubmit={this.handleSubmit} className="space-y-6">
            <div className="p-8 rounded-2xl shadow-sm border border-border bg-white leading-relaxed max-h-[400px] overflow-y-auto">
                {data.indemnity_form}
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-border p-6 space-y-4">
                <FormCheckbox
                    id="indemnity_agreed"
                    name="indemnity_agreed"
                    type="checkbox"
                    label="I agree with the terms outlined in the indemnity form above."
                    placeholder="I agree"
                    onChange={this.handleChange}
                    value={agreed}
                    required={true} />
                
                <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-4 border-t border-border/50">
                    <div className="flex-1"></div>
                    <button
                        id="btn-submit"
                        type="submit"
                        className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg text-sm font-semibold transition-colors bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm disabled:opacity-50"
                        disabled={!agreed || submitting}>
                        {submitting && (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        )}
                        Submit
                    </button>
                </div>
            </div>
        </form>
      </div>
    )
  }
}

export default IndemnityForm;
