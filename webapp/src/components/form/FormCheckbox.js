import React from "react";
import FormGroup from "./FormGroup";
import FormToolTip from "./FormToolTip";
import "./Style.css";
import MarkdownRenderer from "../MarkdownRenderer";

class FormCheckbox extends React.Component {
  shouldDisplayError = () => {
    return this.props.showError && this.props.errorText !== "";
  };

  componentWillReceiveProps(nextProps) {
    if (nextProps.showFocus) {
      this.nameInput.focus();
    }
  }

  render() {
    return (
      <div>
        <FormGroup
          id={this.props.id + "-group"}
          errorText={this.props.errorText}
        >
          {/* Checkbox beside its label, not a full-width `form-control` under a
              separate label block - that styles a checkbox like a text input, so
              it stretched and ended up floating in the middle of the row. */}
          <div className="flex items-start gap-2 text-left">
            <input
              id={this.props.id}
              className={`mt-0.5 w-4 h-4 shrink-0 cursor-pointer accent-primary${
                this.shouldDisplayError() ? " outline outline-1 outline-error" : ""
              }`}
              type="checkbox"
              placeholder={this.props.placeholder}
              checked={this.props.value}
              onChange={this.props.onChange}
              disabled={this.props.disabled}
              min={this.props.min || null}
              ref={input => {
                this.nameInput = input;
              }}
              tabIndex={this.props.tabIndex}
              autoFocus={this.props.autoFocus}
              required={this.props.required || null}
            />
            <label htmlFor={this.props.id} className="cursor-pointer m-0 leading-snug">
              <MarkdownRenderer source={this.props.label} />
            </label>
            {this.props.description ? (
              <FormToolTip description={this.props.description} />
            ) : null}
          </div>
        </FormGroup>
      </div>
    );
  }
}
export default FormCheckbox;
