import React from "react";
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";
import "./Style.css";
import { withTranslation } from 'react-i18next';
import { getDownloadURL } from "../../utils/files";
import MarkdownRenderer from "../MarkdownRenderer";

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

    const t = this.props.t;

    return (
      <div>
        <FormGroup
          id={this.props.id + "-group"}
          errorText={this.props.errorText}
        >
            <div className="rowC">
              <MarkdownRenderer source={this.props.label}/>
                {this.props.description ? (
                <FormToolTip description={this.props.description} />
                ) : (
                <div />
                )}
            </div>
            <input
                id={this.props.id}
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
                accept={this.props.options && this.props.options.accept ? this.props.options.accept : ".pdf, application/pdf" }
                tabIndex={this.props.tabIndex}
                autoFocus={this.props.autoFocus}
                required={this.props.required || null}
                disabled={this.props.uploading}
            />
            {this.props.uploading && <div class="progress">
                <div class="progress-bar" role="progressbar" style={progressStyle} aria-valuemin="0" aria-valuemax="100"></div>
            </div>}
            {(this.props.uploaded || this.props.value) && 
              <a href={getDownloadURL(this.props.value)} class="text-success uploaded-status">{t('Uploaded file')}</a>}
        </FormGroup>
      </div>
    );
  }
}

export default withTranslation()(FormFileUpload);
