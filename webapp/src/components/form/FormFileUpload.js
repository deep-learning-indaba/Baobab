import React from "react";
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";
import "./Style.css";

const baseUrl = process.env.REACT_APP_API_URL;

class FormFileUpload extends React.Component {
  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.nameInput.focus();
    }
  }

  onChange = event => {
      if (this.props.uploadFile) {
        this.props.uploadFile(event.target.files[0]);
      }
  }

  render() {
    var progressStyle = {
        width: this.props.uploadPercentComplete.toString() + "%"
    };

    return (
      <div>
        <FormGroup
          id={this.props.Id + "-group"}
          errorText={this.props.errorText}
        >
            <div className="rowC">
                <label htmlFor={this.props.id}>{this.props.label}</label>
                {this.props.description ? (
                <FormToolTip description={this.props.description} />
                ) : (
                <div />
                )}
            </div>
            <input
                id={this.props.Id}
                className={
                this.shouldDisplayError()
                    ? "form-control is-invalid"
                    : "form-control"
                }
                type="file"
                placeholder={this.props.placeholder}
                onChange={this.onChange}
                min={this.props.min || null}
                ref={input => {
                this.nameInput = input;
                }}
                accept=".pdf, application/pdf"
                tabIndex={this.props.tabIndex}
                autoFocus={this.props.autoFocus}
                required={this.props.required || null}
                disabled={this.props.uploading}
            />
            {this.props.uploading && <div class="progress">
                <div class="progress-bar" role="progressbar" style={progressStyle} aria-valuemin="0" aria-valuemax="100"></div>
            </div>}
            {(this.props.uploaded || this.props.value) && 
              <a href={baseUrl + "/api/v1/file?filename=" + this.props.value} class="text-success uploaded-status">Uploaded file</a>}
        </FormGroup>
      </div>
    );
  }
}

export default FormFileUpload;
